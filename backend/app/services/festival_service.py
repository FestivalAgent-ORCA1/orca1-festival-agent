"""축제 조회 (담당 BE1). API·AI Tool·BE2 기능(찜·일정·게시글)이 함께 쓴다.

BE2에서 쓰는 함수
- get_festival_or_404(db, content_id): 없으면 404 FESTIVAL_NOT_FOUND
- to_summary(festival, liked_ids): FestivalSummary 모양 dict
- summaries_by_ids(db, content_ids, liked_ids): 여러 개를 한 번에 (순서 유지)
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.constants import REGION_NAMES
from app.core.errors import AppError
from app.models.festival import Festival, FestivalTag

KST = ZoneInfo("Asia/Seoul")
SIMILAR_LIMIT = 6
SORTS = {
    "start_date": (Festival.start_date, Festival.content_id),
    "end_date": (Festival.end_date, Festival.content_id),
    "title": (Festival.title, Festival.content_id),
}


def today_kst() -> date:
    """서버 시간대(Render 기본 UTC)와 상관없이 한국 날짜"""
    return datetime.now(KST).date()


def festival_status(start: date, end: date, today: date | None = None) -> str:
    today = today or today_kst()
    if end < today:
        return "ended"
    if start > today:
        return "upcoming"
    return "ongoing"


def https_url(url: str | None) -> str | None:
    """TourAPI 이미지가 http로 오는 경우가 있어 https로 바꿔 줌 (배포 사이트의 혼합 콘텐츠 방지)"""
    if not url:
        return None
    return "https://" + url[len("http://"):] if url.startswith("http://") else url


def _float(value) -> float | None:
    return float(value) if value is not None else None


def to_summary(festival: Festival, liked_ids: set[str] | frozenset[str] = frozenset()) -> dict:
    return {
        "content_id": festival.content_id,
        "title": festival.title,
        "start_date": festival.start_date,
        "end_date": festival.end_date,
        "status": festival_status(festival.start_date, festival.end_date),
        "area_code": festival.area_code,
        "area_name": REGION_NAMES.get(festival.area_code or ""),
        "address": festival.address,
        "image_url": https_url(festival.image_url),
        "lng": _float(festival.lng),
        "lat": _float(festival.lat),
        "tags": festival.tag_codes,
        "is_liked": festival.content_id in liked_ids,
    }


def to_detail(festival: Festival, liked_ids: set[str] | frozenset[str] = frozenset()) -> dict:
    return {
        **to_summary(festival, liked_ids),
        "overview": festival.overview,
        "place": festival.place,
        "playtime": festival.playtime,
        "fee": festival.fee,
        "tel": festival.tel,
        "homepage": festival.homepage,
    }


def get_festival_or_404(db: Session, content_id: str) -> Festival:
    festival = db.get(Festival, content_id)
    if festival is None:
        raise AppError(404, "FESTIVAL_NOT_FOUND", "축제를 찾을 수 없어요.")
    return festival


def summaries_by_ids(
    db: Session, content_ids: list[str], liked_ids: set[str] | frozenset[str] = frozenset()
) -> list[dict]:
    """요청한 순서대로 FestivalSummary 목록. DB에 없는 ID는 건너뜀"""
    if not content_ids:
        return []
    rows = db.scalars(select(Festival).where(Festival.content_id.in_(content_ids))).all()
    by_id = {f.content_id: f for f in rows}
    return [to_summary(by_id[i], liked_ids) for i in content_ids if i in by_id]


def _split(value: str | None) -> list[str]:
    return [v.strip() for v in (value or "").split(",") if v.strip()]


def list_festivals(
    db: Session,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    area_code: str | None = None,
    tags: str | None = None,
    status: str | None = None,
    keyword: str | None = None,
    sort: str = "start_date",
    page: int = 1,
    size: int = 20,
    liked_ids: set[str] | frozenset[str] = frozenset(),
) -> dict:
    today = today_kst()
    if start_date and end_date and end_date < start_date:
        raise AppError(400, "BAD_REQUEST", "종료일이 시작일보다 빨라요.")

    conditions = [
        Festival.end_date >= (start_date or today),
        Festival.end_date >= today,  # 종료된 축제는 항상 제외
    ]
    if end_date:
        conditions.append(Festival.start_date <= end_date)
    if codes := _split(area_code):
        conditions.append(Festival.area_code.in_(codes))
    if tag_codes := _split(tags):
        conditions.append(
            Festival.content_id.in_(
                select(FestivalTag.content_id).where(FestivalTag.tag_code.in_(tag_codes))
            )
        )
    if status == "upcoming":
        conditions.append(Festival.start_date > today)
    elif status == "ongoing":
        conditions.append(Festival.start_date <= today)
    if keyword and (word := "".join(keyword.split())):
        # 축제명·주소 검색, 공백 무시 (예: "빛 초롱" == "빛초롱")
        escaped = word.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped}%"
        conditions.append(
            or_(
                func.replace(Festival.title, " ", "").like(pattern, escape="\\"),
                func.replace(func.coalesce(Festival.address, ""), " ", "").like(
                    pattern, escape="\\"
                ),
            )
        )

    total = db.scalar(select(func.count()).select_from(Festival).where(*conditions)) or 0
    rows = db.scalars(
        select(Festival)
        .where(*conditions)
        .order_by(*SORTS.get(sort, SORTS["start_date"]))
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    return {
        "items": [to_summary(f, liked_ids) for f in rows],
        "page": page,
        "size": size,
        "total": total,
    }


def get_detail(db: Session, content_id: str, liked_ids: set[str] | frozenset[str] = frozenset()) -> dict:
    return to_detail(get_festival_or_404(db, content_id), liked_ids)


def similar_festivals(
    db: Session,
    content_id: str,
    limit: int = SIMILAR_LIMIT,
    liked_ids: set[str] | frozenset[str] = frozenset(),
) -> list[dict]:
    """태그가 많이 겹치는 순 → 같은 지역 우선 → 빨리 시작하는 순. 종료된 축제·자기 자신 제외"""
    base = get_festival_or_404(db, content_id)
    tag_codes = base.tag_codes
    today = today_kst()
    open_condition = [Festival.end_date >= today, Festival.content_id != content_id]

    if tag_codes:
        overlap = func.count(FestivalTag.tag_code).label("overlap")
        same_area = (Festival.area_code == base.area_code) if base.area_code else None
        query = (
            select(Festival)
            .join(FestivalTag, FestivalTag.content_id == Festival.content_id)
            .where(*open_condition, FestivalTag.tag_code.in_(tag_codes))
            .group_by(Festival.content_id)
            .order_by(overlap.desc())
        )
        if same_area is not None:
            query = query.order_by(func.max(same_area).desc())
        query = query.order_by(Festival.start_date, Festival.content_id).limit(limit)
    elif base.area_code:
        query = (
            select(Festival)
            .where(*open_condition, Festival.area_code == base.area_code)
            .order_by(Festival.start_date, Festival.content_id)
            .limit(limit)
        )
    else:
        return []
    return [to_summary(f, liked_ids) for f in db.scalars(query).all()]
