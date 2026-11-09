from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.schedule import Schedule, ScheduleItem
from app.models.user import User
from app.schemas.schedule import (
    ScheduleCreateRequest, ScheduleDetailResponse, ScheduleItemIn, ScheduleListItemResponse,
)


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


def to_detail_response(db: Session, schedule: Schedule) -> ScheduleDetailResponse:
    items = [
        ScheduleItemIn(
            seq=i.seq, category=i.category, content_id=i.content_id, name=i.name,
            address=i.address, lng=i.lng, lat=i.lat,
            start_time=i.start_time, end_time=i.end_time,
            travel_min_from_prev=i.travel_min_from_prev,
            distance_km_from_prev=i.distance_km_from_prev, memo=i.memo,
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
        festival=None,  # TODO(BE1 연동): FestivalSummary
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
    if data.end_time <= data.start_time:
        raise AppError(400, "BAD_REQUEST", "종료 시각이 시작 시각보다 빨라요.")
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
    if data.end_time <= data.start_time:
        raise AppError(400, "BAD_REQUEST", "종료 시각이 시작 시각보다 빨라요.")
    schedule.title = data.title
    schedule.festival_content_id = data.festival_content_id
    schedule.visit_date = data.visit_date
    schedule.start_time = data.start_time
    schedule.end_time = data.end_time
    schedule.total_travel_min = data.total_travel_min
    db.query(ScheduleItem).filter(ScheduleItem.schedule_id == schedule.id).delete()
    _add_items(db, schedule.id, data.items)
    db.commit()
    db.refresh(schedule)
    return schedule


def get_schedule(db: Session, user: User, schedule_id: int) -> Schedule:
    return _get_owned_schedule(db, user, schedule_id)


def delete_schedule(db: Session, user: User, schedule_id: int) -> None:
    schedule = _get_owned_schedule(db, user, schedule_id)
    db.delete(schedule)             # schedule_items는 ON DELETE CASCADE로 함께 삭제
    db.commit()


def list_schedules(db: Session, user: User, page: int, size: int) -> tuple[list, int]:
    total = db.scalar(select(func.count()).select_from(Schedule).where(Schedule.user_id == user.id))
    schedules = db.scalars(
        select(Schedule).where(Schedule.user_id == user.id)
        .order_by(Schedule.visit_date.desc())
        .offset((page - 1) * size).limit(size)
    ).all()
    items = []
    for s in schedules:
        count = db.scalar(select(func.count()).select_from(ScheduleItem).where(ScheduleItem.schedule_id == s.id))
        items.append(ScheduleListItemResponse(
            id=s.id, title=s.title, visit_date=s.visit_date,
            festival=None,          # TODO(BE1 연동): FestivalSummary
            item_count=count,
        ))
    return items, total