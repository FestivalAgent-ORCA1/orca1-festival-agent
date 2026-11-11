"""/api/festivals — 축제 목록·상세·비슷한 축제 (docs/api-spec.md 4장)"""

from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user, get_current_user_optional
from app.models.user import User
from app.schemas.festival import FestivalDetail, FestivalPage, FestivalSummary, RecommendedFestival
from app.services import festival_service, recommend_service
from app.services.like_service import list_liked_ids

router = APIRouter(prefix="/api/festivals", tags=["festivals"])


def get_liked_ids(
    user: User | None = Depends(get_current_user_optional), db: Session = Depends(get_db)
) -> frozenset[str]:
    """🔓 로그인했으면 찜한 축제 ID, 아니면 빈 집합 (is_liked 채우기용)"""
    return frozenset(list_liked_ids(db, user)) if user else frozenset()


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
    liked_ids: frozenset[str] = Depends(get_liked_ids),
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
        liked_ids=liked_ids,
    )


# 주의: /recommended는 /{content_id}보다 먼저 등록해야 한다
@router.get("/recommended", response_model=list[RecommendedFestival])
def get_recommended(
    size: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """🔒 맞춤 추천. 첫 설정 전이면 400 ONBOARDING_REQUIRED. reason은 AI가 써서 몇 초 걸릴 수 있음"""
    return recommend_service.recommend(db, user, size)



@router.get("/{content_id}", response_model=FestivalDetail)
def get_festival(
    content_id: str,
    db: Session = Depends(get_db),
    liked_ids: frozenset[str] = Depends(get_liked_ids),
):
    return festival_service.get_detail(db, content_id, liked_ids)


@router.get("/{content_id}/similar", response_model=list[FestivalSummary])
def get_similar(
    content_id: str,
    db: Session = Depends(get_db),
    liked_ids: frozenset[str] = Depends(get_liked_ids),
):
    return festival_service.similar_festivals(db, content_id, liked_ids=liked_ids)
