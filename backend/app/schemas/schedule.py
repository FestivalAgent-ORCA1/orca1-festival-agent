from datetime import date, datetime, time

from pydantic import BaseModel, Field, field_serializer


class TimeHHMM(BaseModel):
    """시각을 api-spec 형식 "HH:MM"으로 응답하기 위한 공통 부모 클래스"""

    @field_serializer("start_time", "end_time", check_fields=False)
    def _format_time(self, value: time) -> str:
        return value.strftime("%H:%M")


class ScheduleItemIn(TimeHHMM):
    """시간표 한 줄 (요청·응답 공통) — api-spec 'Itinerary'의 items"""
    seq: int = Field(ge=1)
    category: str                             # festival / attraction / restaurant / cafe
    content_id: str | None = None             # 사용자가 직접 넣은 장소면 null
    name: str = Field(max_length=200)
    address: str | None = None
    lng: float | None = None
    lat: float | None = None
    start_time: time
    end_time: time
    travel_min_from_prev: int | None = None   # 첫 장소는 null
    distance_km_from_prev: float | None = None
    memo: str | None = Field(default=None, max_length=300)


class ScheduleCreateRequest(TimeHHMM):
    """POST/PUT 요청: Itinerary(warnings 제외) + title"""
    title: str = Field(min_length=1, max_length=100)
    festival_content_id: str
    visit_date: date
    start_time: time
    end_time: time
    total_travel_min: int = Field(ge=0, default=0)
    items: list[ScheduleItemIn] = Field(min_length=1)


class ScheduleDetailResponse(TimeHHMM):
    id: int
    title: str
    festival_content_id: str
    visit_date: date
    start_time: time
    end_time: time
    total_travel_min: int
    items: list[ScheduleItemIn]
    festival: dict | None = None   # TODO(BE1 연동): FestivalSummary로 교체
    created_at: datetime


class ScheduleListItemResponse(BaseModel):
    """GET /api/schedules 목록 항목"""
    id: int
    title: str
    visit_date: date
    festival: dict | None = None   # TODO(BE1 연동): FestivalSummary로 교체
    item_count: int