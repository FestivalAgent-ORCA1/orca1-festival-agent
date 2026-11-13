"""Tool: search_festivals — 기간·지역·태그로 축제 찾기 (docs/tool-spec.md 1번)

sync_festivals가 축제를 DB에 저장하므로 TourAPI를 직접 부르지 않고 우리 DB(festivals)를 조회한다.
"""

from datetime import date, timedelta

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.core.constants import REGION_CODES, TAG_CODES
from app.core.errors import AppError
from app.services import festival_service

DEFAULT_DAYS = 30
MAX_LIMIT = 50


def _parse(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def search_festivals(
    db: Session,
    start_date: str,
    end_date: str | None = None,
    area_codes: list[str] | None = None,
    tags: list[str] | None = None,
    keyword: str | None = None,
    limit: int = 20,
    *,
    liked_ids: frozenset[str] = frozenset(),
) -> dict:
    """{"ok": True, "festivals": [FestivalSummary], "total": n}. 실패해도 예외 대신 {"ok": False, ...}"""
    try:
        start = _parse(start_date) or festival_service.today_kst()
        end = _parse(end_date) or start + timedelta(days=DEFAULT_DAYS)
    except ValueError:
        return {"ok": False, "error": {"code": "BAD_REQUEST", "message": "날짜는 YYYY-MM-DD 형식이어야 해요."}}
    # AI가 목록에 없는 코드를 보내면 버림
    areas = [c for c in (area_codes or []) if c in REGION_CODES]
    tag_codes = [t for t in (tags or []) if t in TAG_CODES]
    try:
        page = festival_service.list_festivals(
            db,
            start_date=start,
            end_date=end,
            area_code=",".join(areas) or None,
            tags=",".join(tag_codes) or None,
            keyword=(keyword or "").strip()[:50] or None,
            size=max(1, min(int(limit or 20), MAX_LIMIT)),
            liked_ids=liked_ids,
        )
    except AppError as exc:
        return {"ok": False, "error": {"code": exc.code, "message": exc.message}}
    return {"ok": True, "festivals": jsonable_encoder(page["items"]), "total": page["total"]}
