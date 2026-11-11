"""일정 계산 (docs/workflow.md ③, POST /api/itinerary/calculate와 AI 채팅 일정 경로가 함께 사용)

순서가 항상 같아서 AI에게 맡기지 않고 코드로 고정:
1. get_festival_detail → 2. 주변 장소(사용자가 고른 것 + 자동 채우기) → 3. build_timeline(직선거리 추정)
→ 4. calc_travel_time(이웃한 쌍만) → 5. build_timeline(실제 이동 시간) → 6. validate_schedule
   └ errors가 있으면 장소를 하나 빼고 3번부터 다시 (최대 2회)
"""

import logging
from datetime import date

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.services.festival_service import today_kst
from app.tools import tourapi_client
from app.tools.build_timeline import build_timeline, meal_windows, to_min
from app.tools.calc_travel_time import compute_legs
from app.tools.get_festival_detail import get_festival_detail
from app.tools.search_nearby_places import find_places
from app.tools.validate_schedule import validate_schedule

logger = logging.getLogger(__name__)

MIN_DURATION_MIN = 120  # 축제 1곳(120분)은 들어가야 함
AUTO_FILL_ATTRACTIONS = 2
AUTO_FILL_CAFES = 1
MAX_REBUILD = 2
LEG_ROUNDS = 2  # 다시 배치하면서 이웃이 바뀐 쌍의 이동 시간을 한 번 더 계산


def _nearby(festival: dict) -> dict[str, list[dict]]:
    """카테고리별 주변 장소 (가까운 순). TourAPI 실패는 빈 목록 + 경고"""
    if festival.get("lng") is None or festival.get("lat") is None:
        return {}
    result = {}
    for category in ("attraction", "restaurant", "cafe"):
        try:
            places = find_places(festival["lng"], festival["lat"], category)
        except tourapi_client.TourApiError as exc:
            logger.warning("주변 장소 실패 %s: %s", category, exc)
            places = []
        result[category] = [p for p in places if p["content_id"] != festival["content_id"]]
    return result


def choose_places(
    festival: dict, place_ids: list[str], auto_fill: bool, start: int, end: int,
    extra_categories: list[str] | None = None,
) -> tuple[list[dict], bool]:
    """(일정에 넣을 장소, 주변 장소를 못 가져왔는지)

    auto_fill: 식사 시간대 수만큼 식당, 관광지 2, 카페 1까지 가까운 순으로 채움
    extra_categories: 이미 있는 것에 더해 한 곳씩 추가 (AI 채팅의 "카페 추가해줘")
    """
    extra_categories = [c for c in extra_categories or [] if c in ("attraction", "restaurant", "cafe")]
    if not place_ids and not auto_fill and not extra_categories:
        return [], False
    nearby = _nearby(festival)
    if not any(nearby.values()):
        return [], True
    by_id = {p["content_id"]: p for places in nearby.values() for p in places}
    chosen = [by_id[i] for i in dict.fromkeys(place_ids) if i in by_id]
    have = {c: sum(1 for p in chosen if p["category"] == c) for c in ("attraction", "restaurant", "cafe")}
    want = dict(have)
    if auto_fill:
        want["restaurant"] = max(want["restaurant"], len(meal_windows(start, end)))
        want["attraction"] = max(want["attraction"], AUTO_FILL_ATTRACTIONS)
        want["cafe"] = max(want["cafe"], AUTO_FILL_CAFES)
    for category in extra_categories:
        want[category] += 1
    for category, count in want.items():
        for p in nearby.get(category, []):
            if have[category] >= count:
                break
            if p not in chosen:
                chosen.append(p)
                have[category] += 1
    return chosen, False


def _pairs(itinerary: dict, known: set[tuple[str, str]]) -> list[dict]:
    items = itinerary["items"]
    legs = []
    for a, b in zip(items, items[1:]):
        if (a["content_id"], b["content_id"]) in known:
            continue
        if None in (a["lng"], a["lat"], b["lng"], b["lat"]):
            continue
        legs.append({"from": {k: a[k] for k in ("content_id", "lng", "lat")},
                     "to": {k: b[k] for k in ("content_id", "lng", "lat")}})
    return legs


def _arrange(db: Session, festival: dict, places: list[dict], visit: str, start_time: str, end_time: str) -> dict:
    """3~5번: 추정 배치 → 이웃한 쌍만 실제 이동 시간 → 다시 배치"""
    legs: list[dict] = []
    itinerary = build_timeline(festival, places, visit, start_time, end_time)["itinerary"]
    for _ in range(LEG_ROUNDS):
        pairs = _pairs(itinerary, {(l["from_content_id"], l["to_content_id"]) for l in legs})
        if not pairs:
            break
        legs += compute_legs(db, pairs)
        itinerary = build_timeline(festival, places, visit, start_time, end_time, legs)["itinerary"]
    return itinerary


def calculate(
    db: Session,
    festival_content_id: str,
    visit_date: date,
    start_time: str,
    end_time: str,
    place_ids: list[str] | None = None,
    auto_fill: bool = True,
    *,
    extra_categories: list[str] | None = None,
) -> dict:
    """Itinerary. 만들 수 없으면 AppError (404 FESTIVAL_NOT_FOUND, 400 VISIT_DATE_OUT_OF_RANGE / TIME_TOO_SHORT)"""
    detail = get_festival_detail(db, festival_content_id)
    if not detail["ok"]:
        raise AppError(404, "FESTIVAL_NOT_FOUND", "축제를 찾을 수 없어요.")
    festival = detail["festival"]
    if not (date.fromisoformat(festival["start_date"]) <= visit_date <= date.fromisoformat(festival["end_date"])):
        raise AppError(400, "VISIT_DATE_OUT_OF_RANGE",
                       f"방문일이 축제 기간({festival['start_date']}~{festival['end_date']})이 아니에요.")
    if visit_date < today_kst():
        raise AppError(400, "VISIT_DATE_OUT_OF_RANGE", "지난 날짜로는 일정을 만들 수 없어요.")
    start, end = to_min(start_time), to_min(end_time)
    if end - start < MIN_DURATION_MIN:
        raise AppError(400, "TIME_TOO_SHORT", "일정 시간이 너무 짧아요. 최소 2시간 이상으로 정해 주세요.")

    places, unavailable = choose_places(festival, place_ids or [], auto_fill, start, end, extra_categories)
    visit = visit_date.isoformat()
    for attempt in range(MAX_REBUILD + 1):
        itinerary = _arrange(db, festival, places, visit, start_time, end_time)
        check = validate_schedule(itinerary, festival)
        if check["valid"]:
            break
        removable = [p for p in places if p["content_id"] in {i["content_id"] for i in itinerary["items"]}] or places
        if attempt == MAX_REBUILD or not removable:
            code = check["errors"][0]["code"]
            if code == "EXCEEDS_END_TIME":
                raise AppError(400, "TIME_TOO_SHORT", "정한 시간 안에 일정을 넣지 못했어요. 종료 시각을 늦춰 주세요.")
            raise AppError(400, code, check["errors"][0]["message"])
        places = [p for p in places if p is not removable[-1]]  # 마지막에 넣은 장소부터 뺌

    warnings = [{"code": w["code"], "message": w["message"]} for w in check["warnings"]]
    if unavailable:
        warnings.append({"code": "PLACES_UNAVAILABLE", "message": "주변 장소 정보를 가져오지 못해 축제 위주로 만들었어요."})
    return {**itinerary, "warnings": warnings}
