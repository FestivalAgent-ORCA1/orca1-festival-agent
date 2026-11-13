"""Tool: validate_schedule — 시간표 검사 (계산만, docs/tool-spec.md 7번)

errors가 있으면 valid=False → itinerary_service가 장소를 빼고 다시 배치 (최대 2회)
warnings는 Itinerary.warnings로 전달 (build_timeline이 넣은 경고도 유지)
"""

from datetime import date

from app.tools.build_timeline import DEFAULT_PLAYTIME, meal_windows, parse_playtime, to_min

LONG_TRAVEL_MIN = 60


def _err(code: str, message: str, seq: int | None = None) -> dict:
    return {"code": code, "message": message, "seq": seq}


def validate_schedule(itinerary: dict, festival: dict) -> dict:
    errors: list[dict] = []
    warnings: list[dict] = [dict(w) for w in itinerary.get("warnings") or []]
    items = itinerary.get("items") or []

    visit = date.fromisoformat(str(itinerary["visit_date"]))
    if not (date.fromisoformat(str(festival["start_date"])) <= visit <= date.fromisoformat(str(festival["end_date"]))):
        errors.append(_err("VISIT_DATE_OUT_OF_RANGE", "방문일이 축제 기간이 아니에요."))

    fest_items = [i for i in items if i["category"] == "festival"]
    if not fest_items:
        errors.append(_err("FESTIVAL_MISSING", "시간표에 축제가 없어요."))

    for a, b in zip(items, items[1:]):
        if to_min(a["end_time"]) > to_min(b["start_time"]):
            errors.append(_err("TIME_OVERLAP", f"{a['name']}와 {b['name']}의 시간이 겹쳐요.", b["seq"]))
    if items and to_min(items[-1]["end_time"]) > to_min(itinerary["end_time"]):
        errors.append(_err("EXCEEDS_END_TIME", "마지막 장소가 종료 시각을 넘겨요.", items[-1]["seq"]))

    playtime = parse_playtime(festival.get("playtime"))
    if playtime is None and not any(w["code"] == "FESTIVAL_TIME_UNKNOWN" for w in warnings):
        warnings.append(_err("FESTIVAL_TIME_UNKNOWN", "축제 운영 시간 정보가 없어 가정한 시간을 썼어요."))
    f_open, f_close = playtime or DEFAULT_PLAYTIME
    for item in fest_items:
        if to_min(item["start_time"]) < f_open or to_min(item["end_time"]) > f_close:
            warnings.append(_err("OUTSIDE_PLAYTIME", "축제 운영 시간 밖에 배치됐어요. 운영 시간을 확인해 주세요.", item["seq"]))

    for prev, item in zip(items, items[1:]):
        if (item.get("travel_min_from_prev") or 0) > LONG_TRAVEL_MIN:
            warnings.append(_err("LONG_TRAVEL", f"{prev['name']} → {item['name']} 이동이 60분 넘게 걸려요.", item["seq"]))

    start, end = to_min(itinerary["start_time"]), to_min(itinerary["end_time"])
    for meal_start, meal_end in meal_windows(start, end):
        has_meal = any(
            i["category"] == "restaurant"
            and to_min(i["start_time"]) < meal_end and to_min(i["end_time"]) > meal_start
            for i in items
        )
        if not has_meal:
            label = "점심" if meal_start < 15 * 60 else "저녁"
            warnings.append(_err("NO_MEAL", f"{label} 시간에 식당이 없어요. 축제장 먹거리를 이용해 보세요."))

    # 같은 경고가 두 번 나오지 않게 (code+seq 기준)
    unique, seen = [], set()
    for w in warnings:
        key = (w["code"], w.get("seq"))
        if key not in seen:
            seen.add(key)
            unique.append({"code": w["code"], "message": w["message"], "seq": w.get("seq")})
    return {"ok": True, "valid": not errors, "errors": errors, "warnings": unique}
