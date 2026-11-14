"""Tool: build_timeline — 방문 순서와 시간표 (계산만, docs/tool-spec.md 6번)

배치 방식 (시간을 앞에서부터 흘려보내며 하나씩 놓음)
- '기준점(anchor)': 축제(운영 시작 시각), 점심 식당(11:30), 저녁 식당(17:30)
- 기준점 사이 빈 시간에 관광지·카페를 직전 장소에서 가까운 순으로 채움 (nearest neighbor, 직선거리)
- 장소 사이: 이동 시간 + 여유 5분, 시작 시각은 5분 단위로 올림
- 종료 시각 안에 못 들어가는 관광지·카페는 뺌. 축제는 항상 넣음 (넘치면 validate_schedule이 오류로 잡음)
- 이동 시간은 travel_legs(calc_travel_time 결과)가 있으면 사용, 없으면 직선거리로 추정 → warnings에 TRAVEL_ESTIMATED
"""

import math
import re
from dataclasses import dataclass

from app.tools.calc_travel_time import estimate

STAY_MIN = {"festival": 120, "attraction": 60, "restaurant": 60, "cafe": 40}
LUNCH, DINNER = (690, 810), (1050, 1170)  # 11:30~13:30, 17:30~19:30 (분)
MEAL_MIN_OVERLAP = 60  # 일정 시간과 식사 시간대가 이만큼 겹쳐야 식사를 넣음
NIGHT_FROM = 17 * 60
DEFAULT_PLAYTIME = (10 * 60, 18 * 60)  # 운영 시간을 모를 때 가정
BUFFER_MIN = 5
FILLER_SLACK_MIN = 30  # 식사 시작을 이만큼까지는 늦춰도 관광지를 먼저 넣음
NEAR_KM = 0.1  # 이보다 가까운 이동은 추정값이어도 TRAVEL_ESTIMATED 경고를 내지 않음


# ---- 시각 변환 ----


def to_min(value: str) -> int:
    h, m = value.split(":")
    return int(h) * 60 + int(m)


def to_hhmm(minutes: int) -> str:
    minutes = max(0, min(minutes, 24 * 60 - 1))
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def round5(minutes: float) -> int:
    return int(math.ceil(minutes / 5) * 5)


def parse_playtime(text: str | None) -> tuple[int, int] | None:
    """'10:00~18:00', '17:00 ~ 22:00', '10시~18시' → (여는 분, 닫는 분). 못 읽으면 None"""
    if not text:
        return None
    m = re.search(r"(\d{1,2}):(\d{2})\s*[~\-–〜]\s*(\d{1,2}):(\d{2})", text)
    if m:
        open_, close = int(m[1]) * 60 + int(m[2]), int(m[3]) * 60 + int(m[4])
    else:
        m = re.search(r"(\d{1,2})\s*시\s*[~\-–〜]\s*(\d{1,2})\s*시", text)
        if not m:
            return None
        open_, close = int(m[1]) * 60, int(m[2]) * 60
    if open_ >= 24 * 60:
        return None
    if close <= open_:  # 자정을 넘기는 축제 (18:00~02:00)
        close = 24 * 60 - 1
    return open_, min(close, 24 * 60 - 1)


def meal_windows(start: int, end: int) -> list[tuple[int, int]]:
    return [(s, e) for s, e in (LUNCH, DINNER) if min(e, end) - max(s, start) >= MEAL_MIN_OVERLAP]


# ---- 배치 ----


@dataclass
class Stop:
    category: str
    data: dict  # Place 또는 FestivalDetail
    anchor: int | None = None  # 이 시각 이후에 시작 (기준점)
    latest: int | None = None  # 이 시각까지는 시작해야 함 (식사)

    @property
    def id(self) -> str:
        return str(self.data.get("content_id"))

    def coords(self) -> tuple[float, float] | None:
        lng, lat = self.data.get("lng"), self.data.get("lat")
        return (float(lng), float(lat)) if lng is not None and lat is not None else None


class Travel:
    def __init__(self, legs: list[dict] | None):
        self.known = {(l["from_content_id"], l["to_content_id"]): l for l in legs or []}

    def between(self, a: Stop, b: Stop) -> tuple[int, float | None, bool]:
        """(분, km, 추정값 여부)"""
        leg = self.known.get((a.id, b.id))
        if leg:
            return int(leg["duration_min"]), float(leg["distance_km"]), leg.get("source") == "estimate"
        ca, cb = a.coords(), b.coords()
        if ca and cb:
            minutes, km = estimate(*ca, *cb)
            return minutes, km, True
        return 15, None, True  # 좌표가 없으면 15분으로 가정


def _distance(a: Stop, b: Stop) -> float:
    ca, cb = a.coords(), b.coords()
    if not ca or not cb:
        return float("inf")
    return (ca[0] - cb[0]) ** 2 + (ca[1] - cb[1]) ** 2


def build_timeline(
    festival: dict,
    places: list[dict],
    visit_date: str,
    start_time: str,
    end_time: str,
    travel_legs: list[dict] | None = None,
) -> dict:
    """{"ok": True, "itinerary": Itinerary}. Itinerary 모양은 docs/api-spec.md"""
    start, end = to_min(start_time), to_min(end_time)
    warnings: list[dict] = []
    playtime = parse_playtime(festival.get("playtime"))
    if playtime is None:
        playtime = DEFAULT_PLAYTIME
        warnings.append({"code": "FESTIVAL_TIME_UNKNOWN",
                         "message": f"축제 운영 시간 정보가 없어 {to_hhmm(playtime[0])}~{to_hhmm(playtime[1])}로 가정했어요."})
    f_open, f_close = playtime

    fest = Stop("festival", festival, anchor=max(start, f_open))
    if f_open >= NIGHT_FROM:  # 야간 축제는 저녁 이후로
        fest.anchor = max(f_open, start)
    anchors: list[Stop] = [fest]

    restaurants = [Stop("restaurant", p) for p in places if p.get("category") == "restaurant"]
    fillers = [Stop(p["category"], p) for p in places if p.get("category") in ("attraction", "cafe")]
    for meal_start, meal_end in meal_windows(start, end):
        if not restaurants:
            break
        # 식사 시간대에 가까운 식당: 축제와 가까운 순 (사용자가 고른 식당이 먼저)
        r = restaurants.pop(0)
        r.anchor, r.latest = max(meal_start, start), meal_end - STAY_MIN["restaurant"]
        anchors.append(r)
    fillers += restaurants  # 식사 시간대보다 많은 식당은 일반 장소처럼 (자리가 있으면)
    anchors.sort(key=lambda s: (s.anchor, 0 if s.category == "festival" else 1))

    travel = Travel(travel_legs)
    items: list[dict] = []
    now, prev, estimated = start, None, False

    def arrival(stop: Stop) -> tuple[int, int | None, float | None, bool]:
        if prev is None:
            return start, None, None, False
        minutes, km, is_estimate = travel.between(prev, stop)
        return round5(now + minutes + BUFFER_MIN), minutes, km, is_estimate

    def place(stop: Stop, begin: int, minutes, km, is_estimate: bool) -> None:
        nonlocal now, prev, estimated
        # 50m 이내(걸어서 바로)는 카카오를 부르지 않아 추정값이지만 경고할 필요 없음
        estimated = estimated or (is_estimate and (km is None or km > NEAR_KM))
        stay = STAY_MIN[stop.category]
        if stop.category == "festival":
            stay = max(30, min(stay, f_close - begin)) if begin < f_close else stay
        d = stop.data
        items.append({
            "seq": len(items) + 1,
            "category": stop.category,
            "content_id": stop.id,
            "name": d.get("name") or d.get("title"),
            "address": d.get("address"),
            "lng": d.get("lng"),
            "lat": d.get("lat"),
            "start_time": to_hhmm(begin),
            "end_time": to_hhmm(begin + stay),
            "travel_min_from_prev": minutes,
            "distance_km_from_prev": round(km, 2) if km is not None else None,
            "memo": d.get("place") if stop.category == "festival" else None,
        })
        now, prev = begin + stay, stop

    while anchors or fillers:
        nxt = anchors[0] if anchors else None
        # 1) 다음 기준점 전에 들어가는 가장 가까운 관광지·카페
        chosen = None
        for filler in sorted(fillers, key=lambda s: _distance(prev or fest, s)):
            begin = arrival(filler)[0]
            finish = begin + STAY_MIN[filler.category]
            if finish > end:
                continue
            if nxt is not None:
                slack = FILLER_SLACK_MIN if nxt.category == "restaurant" else 0
                to_next = travel.between(filler, nxt)[0] + BUFFER_MIN
                if finish + to_next > nxt.anchor + slack:
                    continue
            chosen = filler
            break
        if chosen is not None:
            fillers.remove(chosen)
            place(chosen, *arrival(chosen))
            continue
        if nxt is None:
            break  # 남은 관광지·카페는 시간 안에 안 들어감
        # 2) 기준점 배치
        anchors.pop(0)
        begin, minutes, km, is_estimate = arrival(nxt)
        begin = max(begin, nxt.anchor)
        if nxt.category == "restaurant" and (begin > (nxt.latest or end) or begin + STAY_MIN["restaurant"] > end):
            continue  # 식사 시간을 놓침 → 이 식당은 뺌 (validate가 NO_MEAL 경고)
        place(nxt, begin, minutes, km, is_estimate)

    if estimated:
        warnings.append({"code": "TRAVEL_ESTIMATED", "message": "일부 이동 시간은 직선거리로 추정한 값이에요."})
    itinerary = {
        "festival_content_id": str(festival.get("content_id")),
        "visit_date": visit_date,
        "start_time": to_hhmm(start),
        "end_time": to_hhmm(end),
        "total_travel_min": sum(i["travel_min_from_prev"] or 0 for i in items),
        "items": items,
        "warnings": warnings,
    }
    return {"ok": True, "itinerary": itinerary}
