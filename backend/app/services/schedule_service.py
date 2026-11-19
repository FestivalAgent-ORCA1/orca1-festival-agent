from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.schedule import Schedule, ScheduleItem
from app.models.user import User
from app.schemas.schedule import (
    ScheduleCreateRequest, ScheduleDetailResponse, ScheduleItemIn, ScheduleListItemResponse,
)
from app.services import festival_service  # BE1: 축제 조회·FestivalSummary 변환
from app.services.like_service import list_liked_ids


def _get_owned_schedule(db: Session, user: User, schedule_id: int) -> Schedule:
    """내 일정만 가져오기 — 남의 일정이든 없는 일정이든 똑같이 404 (존재 여부 숨김, api-spec)"""
    schedule = db.get(Schedule, schedule_id)
    if schedule is None or schedule.user_id != user.id:
        raise AppError(404, "SCHEDULE_NOT_FOUND", "일정을 찾을 수 없어요.")
    return schedule


def _get_items(db: Session, schedule_id: int) -> list[ScheduleItem]:
    return db.scalars(
        select(ScheduleItem).where(ScheduleItem.schedule_id == schedule_id).order_by(ScheduleItem.seq)
    ).all()


def _festival_summary(db: Session, user: User, content_id: str) -> dict | None:
    summaries = festival_service.summaries_by_ids(db, [content_id], set(list_liked_ids(db, user)))
    return summaries[0] if summaries else None


def _validate(db: Session, data: ScheduleCreateRequest) -> None:
    if data.end_time <= data.start_time:
        raise AppError(400, "BAD_REQUEST", "종료 시각이 시작 시각보다 빨라요.")
    seqs = [item.seq for item in data.items]
    if len(seqs) != len(set(seqs)):
        raise AppError(400, "BAD_REQUEST", "방문 순서(seq)가 겹쳐요.")
    festival_service.get_festival_or_404(db, data.festival_content_id)  # 없는 축제면 404


def to_detail_response(db: Session, schedule: Schedule, user: User) -> ScheduleDetailResponse:
    items = [
        ScheduleItemIn(
            seq=i.seq, category=i.category, content_id=i.content_id, name=i.name,
            address=i.address,
            lng=float(i.lng) if i.lng is not None else None,
            lat=float(i.lat) if i.lat is not None else None,
            start_time=i.start_time, end_time=i.end_time,
            travel_min_from_prev=i.travel_min_from_prev,
            distance_km_from_prev=float(i.distance_km_from_prev) if i.distance_km_from_prev is not None else None,
            memo=i.memo,
        )
        for i in _get_items(db, schedule.id)
    ]
    return ScheduleDetailResponse(
        id=schedule.id, title=schedule.title,
        festival_content_id=schedule.festival_content_id,
        visit_date=schedule.visit_date,
        start_time=schedule.start_time, end_time=schedule.end_time,
        total_travel_min=schedule.total_travel_min,
        items=items,
        festival=_festival_summary(db, user, schedule.festival_content_id),
        created_at=schedule.created_at,
    )


def _add_items(db: Session, schedule_id: int, items: list[ScheduleItemIn]) -> None:
    for item in items:
        db.add(ScheduleItem(
            schedule_id=schedule_id, seq=item.seq, category=item.category,
            content_id=item.content_id, name=item.name, address=item.address,
            lng=item.lng, lat=item.lat,
            start_time=item.start_time, end_time=item.end_time,
            travel_min_from_prev=item.travel_min_from_prev,
            distance_km_from_prev=item.distance_km_from_prev, memo=item.memo,
        ))


def create_schedule(db: Session, user: User, data: ScheduleCreateRequest) -> Schedule:
    _validate(db, data)
    schedule = Schedule(
        user_id=user.id, festival_content_id=data.festival_content_id,
        title=data.title, visit_date=data.visit_date,
        start_time=data.start_time, end_time=data.end_time,
        total_travel_min=data.total_travel_min,
    )
    db.add(schedule)
    db.flush()                      # schedule.id를 먼저 받아옴 (items에 필요)
    _add_items(db, schedule.id, data.items)
    db.commit()
    db.refresh(schedule)
    return schedule


def update_schedule(db: Session, user: User, schedule_id: int, data: ScheduleCreateRequest) -> Schedule:
    """PUT — 다시 계산한 결과로 전체 교체 (api-spec)"""
    schedule = _get_owned_schedule(db, user, schedule_id)
    _validate(db, data)
    schedule.title = data.title
    schedule.festival_content_id = data.festival_content_id
    schedule.visit_date = data.visit_date
    schedule.start_time = data.start_time
    schedule.end_time = data.end_time
    schedule.total_travel_min = data.total_travel_min
    db.query(ScheduleItem).filter(ScheduleItem.schedule_id == schedule.id).delete()
    db.flush()                      # 옛 항목 삭제를 먼저 반영 (seq UNIQUE 충돌 방지)
    _add_items(db, schedule.id, data.items)
    db.commit()
    db.refresh(schedule)
    return schedule


def get_schedule(db: Session, user: User, schedule_id: int) -> Schedule:
    return _get_owned_schedule(db, user, schedule_id)


def delete_schedule(db: Session, user: User, schedule_id: int) -> None:
    schedule = _get_owned_schedule(db, user, schedule_id)
    db.query(ScheduleItem).filter(ScheduleItem.schedule_id == schedule.id).delete()  # CASCADE와 같은 효과를 코드로도 보장
    db.delete(schedule)
    db.commit()


def list_schedules(db: Session, user: User, page: int, size: int) -> tuple[list, int]:
    total = db.scalar(select(func.count()).select_from(Schedule).where(Schedule.user_id == user.id))
    schedules = db.scalars(
        select(Schedule).where(Schedule.user_id == user.id)
        .order_by(Schedule.visit_date.desc(), Schedule.id.desc())
        .offset((page - 1) * size).limit(size)
    ).all()

    # 축제 카드는 한 번에 조회 (일정마다 따로 조회하지 않게)
    liked = set(list_liked_ids(db, user))
    festival_ids = list(dict.fromkeys(s.festival_content_id for s in schedules))
    by_id = {f["content_id"]: f for f in festival_service.summaries_by_ids(db, festival_ids, liked)}

    items = []
    for s in schedules:
        count = db.scalar(select(func.count()).select_from(ScheduleItem).where(ScheduleItem.schedule_id == s.id))
        items.append(ScheduleListItemResponse(
            id=s.id, title=s.title, visit_date=s.visit_date,
            festival=by_id.get(s.festival_content_id),
            item_count=count,
        ))
    return items, total