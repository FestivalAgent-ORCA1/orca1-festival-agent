"""Tool: get_festival_detail — 축제 1개 상세 (docs/tool-spec.md 2번)

DB에 상세가 있고 7일 이내에 받은 것이면 DB 사용, 아니면 TourAPI detailCommon2 + detailIntro2를 불러 DB 갱신.
TourAPI가 실패하면 DB에 있는 내용으로 답한다.
"""

import logging
from datetime import datetime, timedelta

import httpx
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.batch.sync_festivals import apply_detail
from app.models.festival import Festival
from app.services import festival_service
from app.tools import tourapi_client as tour

logger = logging.getLogger(__name__)

FRESH_DAYS = 7


def _is_fresh(festival: Festival) -> bool:
    now = datetime.now(festival_service.KST).replace(tzinfo=None)
    return festival.detail_synced_at is not None and festival.detail_synced_at >= now - timedelta(days=FRESH_DAYS)


def get_festival_detail(
    db: Session, content_id: str, *, liked_ids: frozenset[str] = frozenset(), client: httpx.Client | None = None
) -> dict:
    """{"ok": True, "festival": FestivalDetail}. 없는 축제면 FESTIVAL_NOT_FOUND"""
    festival = db.get(Festival, str(content_id))
    if festival is None:
        return {"ok": False, "error": {"code": "FESTIVAL_NOT_FOUND", "message": "축제를 찾을 수 없어요."}}
    if not _is_fresh(festival):
        owns_client = client is None
        client = client or httpx.Client(timeout=tour.TIMEOUT)
        try:
            apply_detail(client, festival)
            db.commit()
        except tour.TourApiError as exc:
            db.rollback()
            logger.warning("상세 갱신 실패 %s: %s (DB 내용 사용)", content_id, exc)
        finally:
            if owns_client:
                client.close()
    return {"ok": True, "festival": jsonable_encoder(festival_service.to_detail(festival, liked_ids))}
