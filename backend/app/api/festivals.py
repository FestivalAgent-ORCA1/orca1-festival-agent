"""/api/festivals — 축제 목록·상세·비슷한 축제 (docs/api-spec.md 4장)"""

from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.festival import FestivalDetail, FestivalPage, FestivalSummary
from app.services import festival_service

router = APIRouter(prefix="/api/festivals", tags=["festivals"])

# TODO(BE1): BE2 로그인 부품(core/deps.py)과 합친 뒤, 로그인 사용자는 is_liked를 채운다.
NO_LIKES: frozenset[str] = frozenset()


@router.get("", response_model=FestivalPage)
def list_festivals(
    start_date: date | None = None,
    end_date: date | None = None,
    area_code: str | None = Query(None, description="쉼표로 여러 개 (예: 1,31)"),
    tags: str | None = Query(None, description="쉼표로 여러 개, 하나라도 겹치면 포함"),
    status: Literal["upcoming", "ongoing"] | None = None,
    keyword: str | None = Query(None, max_length=50, description="축제명·주소 검색"),
    sort: Literal["start_date", "end_date", "title"] = "start_date",
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    return festival_service.list_festivals(
        db,
        start_date=start_date,
        end_date=end_date,
        area_code=area_code,
        tags=tags,
        status=status,
        keyword=keyword,
        sort=sort,
        page=page,
        size=size,
        liked_ids=NO_LIKES,
    )


# 주의: /recommended는 /{content_id}보다 먼저 등록해야 한다 (3주차에 추가)


@router.get("/{content_id}", response_model=FestivalDetail)
def get_festival(content_id: str, db: Session = Depends(get_db)):
    return festival_service.get_detail(db, content_id, NO_LIKES)


@router.get("/{content_id}/similar", response_model=list[FestivalSummary])
def get_similar(content_id: str, db: Session = Depends(get_db)):
    return festival_service.similar_festivals(db, content_id, liked_ids=NO_LIKES)
