"""축제 응답 모양 (docs/api-spec.md 1장)"""

from datetime import date
from typing import Literal

from pydantic import BaseModel

FestivalStatus = Literal["upcoming", "ongoing", "ended"]


class CodeName(BaseModel):
    code: str
    name: str


class FestivalSummary(BaseModel):
    """축제 카드. 찜·일정 응답에서도 같은 모양을 쓴다."""

    content_id: str
    title: str
    start_date: date
    end_date: date
    status: FestivalStatus
    area_code: str | None
    area_name: str | None
    address: str | None
    image_url: str | None
    lng: float | None
    lat: float | None
    tags: list[str]
    is_liked: bool = False


class FestivalDetail(FestivalSummary):
    overview: str | None
    place: str | None
    playtime: str | None
    fee: str | None
    tel: str | None
    homepage: str | None


class FestivalPage(BaseModel):
    items: list[FestivalSummary]
    page: int
    size: int
    total: int


class RecommendedFestival(FestivalSummary):
    score: int
    reason: str
