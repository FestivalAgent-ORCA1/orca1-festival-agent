"""/api/places — 축제 주변 장소 (docs/api-spec.md 5장)"""

from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import AppError
from app.services import festival_service
from app.tools import tourapi_client
from app.tools.search_nearby_places import DEFAULT_RADIUS, MAX_RADIUS, find_places

router = APIRouter(prefix="/api/places", tags=["places"])


@router.get("/nearby")
def nearby(
    content_id: str,
    category: Literal["attraction", "restaurant", "cafe"],
    radius: int = Query(DEFAULT_RADIUS, ge=100, le=MAX_RADIUS),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    festival = festival_service.get_festival_or_404(db, content_id)
    if festival.lng is None or festival.lat is None:
        return {"items": [], "page": page, "size": size, "total": 0}
    try:
        places = find_places(float(festival.lng), float(festival.lat), category, radius)
    except tourapi_client.TourApiError as exc:
        raise AppError(502, "EXTERNAL_API_ERROR", "주변 장소를 가져오지 못했어요. 잠시 후 다시 시도해 주세요.") from exc
    places = [p for p in places if p["content_id"] != content_id]
    start = (page - 1) * size
    return {"items": places[start : start + size], "page": page, "size": size, "total": len(places)}
