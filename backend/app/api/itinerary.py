"""/api/itinerary — 일정 계산 (저장은 BE2 /api/schedules, docs/api-spec.md 6장)"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.itinerary import Itinerary, ItineraryRequest
from app.services import itinerary_service

router = APIRouter(prefix="/api/itinerary", tags=["itinerary"])


@router.post("/calculate", response_model=Itinerary)
def calculate(body: ItineraryRequest, db: Session = Depends(get_db)):
    """🔓 저장하지 않고 시간표만 계산. 이동 시간 계산 때문에 수 초 걸릴 수 있음"""
    return itinerary_service.calculate(
        db, body.festival_content_id, body.visit_date, body.start_time, body.end_time,
        body.place_ids, body.auto_fill,
    )
