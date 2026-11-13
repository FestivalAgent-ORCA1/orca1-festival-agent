"""POST /api/itinerary/calculate (docs/api-spec.md 6장). 응답 Itinerary 모양은 api-spec 1장"""

from datetime import date

from pydantic import BaseModel, Field

HHMM = r"^([01]\d|2[0-3]):[0-5]\d$"


class ItineraryRequest(BaseModel):
    festival_content_id: str = Field(min_length=1, max_length=20)
    visit_date: date
    start_time: str = Field("10:00", pattern=HHMM)
    end_time: str = Field("21:00", pattern=HHMM)
    place_ids: list[str] = Field(default_factory=list, max_length=10)
    auto_fill: bool = True


class ItineraryItem(BaseModel):
    seq: int
    category: str
    content_id: str | None
    name: str
    address: str | None
    lng: float | None
    lat: float | None
    start_time: str
    end_time: str
    travel_min_from_prev: int | None
    distance_km_from_prev: float | None
    memo: str | None


class Warning_(BaseModel):
    code: str
    message: str


class Itinerary(BaseModel):
    festival_content_id: str
    visit_date: date
    start_time: str
    end_time: str
    total_travel_min: int
    items: list[ItineraryItem]
    warnings: list[Warning_]
