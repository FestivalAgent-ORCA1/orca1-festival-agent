"""일정 계산 — build_timeline·validate_schedule·POST /api/itinerary/calculate (외부 API는 가짜)"""

from datetime import timedelta

import pytest

from app.core.config import settings
from app.models.festival import Festival
from app.services import itinerary_service
from app.services.festival_service import today_kst
from app.tools.build_timeline import build_timeline, parse_playtime
from app.tools.validate_schedule import validate_schedule

FEST = {"content_id": "F", "title": "빛축제", "address": "서울 중구", "lng": 126.978, "lat": 37.566,
        "playtime": "10:00~18:00", "place": "청계천", "start_date": "2026-11-20", "end_date": "2026-11-22"}


def place(cid, category, dlng):
    return {"content_id": cid, "name": cid, "category": category, "address": None,
            "lng": 126.978 + dlng, "lat": 37.566, "image_url": None, "distance_m": 100}


def times(itinerary):
    return [(i["category"], i["start_time"], i["end_time"]) for i in itinerary["items"]]


def test_parse_playtime():
    assert parse_playtime("17:00 ~ 22:00") == (1020, 1320)
    assert parse_playtime("매일 10시~18시") == (600, 1080)
    assert parse_playtime("18:00~02:00") == (1080, 1439)  # 자정 넘김
    assert parse_playtime("상시") is None


def test_day_festival_with_meals_and_fillers():
    places = [place("R1", "restaurant", 0.01), place("R2", "restaurant", 0.02),
              place("A1", "attraction", 0.005), place("C1", "cafe", 0.015)]
    it = build_timeline(FEST, places, "2026-11-21", "10:00", "21:00")["itinerary"]
    cats = [i["category"] for i in it["items"]]
    assert cats[0] == "festival" and it["items"][0]["start_time"] == "10:00" and it["items"][0]["memo"] == "청계천"
    lunch = [i for i in it["items"] if i["content_id"] == "R1"][0]
    dinner = [i for i in it["items"] if i["content_id"] == "R2"][0]
    assert "11:30" <= lunch["start_time"] <= "12:30" and "17:30" <= dinner["start_time"] <= "18:30"
    assert set(cats) == {"festival", "restaurant", "attraction", "cafe"}
    assert all(i["start_time"].endswith(("0", "5")) for i in it["items"])  # 5분 단위
    assert it["items"][1]["travel_min_from_prev"] is not None and it["items"][0]["travel_min_from_prev"] is None
    assert [w["code"] for w in it["warnings"]] == ["TRAVEL_ESTIMATED"]
    assert validate_schedule(it, FEST)["valid"]


def test_night_festival_after_dinner_and_kakao_legs():
    fest = {**FEST, "playtime": "18:00~22:00"}
    places = [place("R1", "restaurant", 0.01)]
    it = build_timeline(fest, places, "2026-11-21", "17:00", "22:00")["itinerary"]
    assert times(it) == [("restaurant", "17:30", "18:30"), ("festival", "18:40", "20:40")]
    legs = [{"from_content_id": "R1", "to_content_id": "F", "duration_min": 20, "distance_km": 3.0, "source": "kakao"}]
    it = build_timeline(fest, places, "2026-11-21", "17:00", "22:00", legs)["itinerary"]
    assert it["items"][1]["start_time"] == "18:55" and it["items"][1]["travel_min_from_prev"] == 20
    assert it["warnings"] == [] and it["total_travel_min"] == 20


def test_unknown_playtime_and_fillers_dropped_when_no_time():
    fest = {**FEST, "playtime": None}
    places = [place(f"A{i}", "attraction", 0.001 * i) for i in range(1, 6)]
    it = build_timeline(fest, places, "2026-11-21", "10:00", "13:00")["itinerary"]
    assert it["warnings"][0]["code"] == "FESTIVAL_TIME_UNKNOWN"
    assert it["items"][-1]["end_time"] <= "13:00"  # 넘치는 관광지는 뺌
    assert len(it["items"]) < 6


def test_validate_errors_and_warnings():
    it = build_timeline(FEST, [], "2026-11-21", "10:00", "21:00")["itinerary"]
    result = validate_schedule(it, FEST)
    assert result["valid"] and {w["code"] for w in result["warnings"]} == {"NO_MEAL"}

    broken = {**it, "visit_date": "2026-12-01", "end_time": "11:00",
              "items": it["items"] + [{**it["items"][0], "seq": 2, "category": "cafe", "name": "카페", "start_time": "11:00",
                                       "end_time": "12:00", "travel_min_from_prev": 70}]}
    result = validate_schedule(broken, FEST)
    codes = {e["code"] for e in result["errors"]}
    assert codes == {"VISIT_DATE_OUT_OF_RANGE", "TIME_OVERLAP", "EXCEEDS_END_TIME"} and not result["valid"]
    assert "LONG_TRAVEL" in {w["code"] for w in result["warnings"]}
    assert "FESTIVAL_MISSING" in {e["code"] for e in validate_schedule({**it, "items": []}, FEST)["errors"]}


# ---- API ----


@pytest.fixture
def festival_today(db, monkeypatch):
    from datetime import datetime
    t = today_kst()
    db.add(Festival(content_id="F", title="빛축제", start_date=t, end_date=t + timedelta(days=2), area_code="1",
                    lng=126.978, lat=37.566, playtime="10:00~18:00", detail_synced_at=datetime.now()))
    db.commit()
    nearby = {"attraction": [place("A1", "attraction", 0.005)], "restaurant": [place("R1", "restaurant", 0.01), place("R2", "restaurant", 0.02)],
              "cafe": [place("C1", "cafe", 0.015)]}
    monkeypatch.setattr(itinerary_service, "find_places", lambda lng, lat, category: nearby[category])
    monkeypatch.setattr(settings, "KAKAO_REST_API_KEY", "")  # 카카오 실패 → 추정값
    return t


def test_calculate_api(client, festival_today):
    body = {"festival_content_id": "F", "visit_date": festival_today.isoformat(), "start_time": "10:00", "end_time": "21:00"}
    res = client.post("/api/itinerary/calculate", json=body)
    assert res.status_code == 200, res.text
    it = res.json()
    assert {i["content_id"] for i in it["items"]} == {"F", "A1", "R1", "R2", "C1"}
    assert "TRAVEL_ESTIMATED" in [w["code"] for w in it["warnings"]]

    only_chosen = client.post("/api/itinerary/calculate", json={**body, "place_ids": ["C1"], "auto_fill": False}).json()
    assert [i["content_id"] for i in only_chosen["items"]] == ["F", "C1"]


def test_calculate_api_errors(client, festival_today):
    base = {"festival_content_id": "F", "visit_date": festival_today.isoformat()}
    assert client.post("/api/itinerary/calculate", json={**base, "festival_content_id": "X"}).json()["code"] == "FESTIVAL_NOT_FOUND"
    out = client.post("/api/itinerary/calculate", json={**base, "visit_date": (festival_today + timedelta(days=10)).isoformat()})
    assert out.status_code == 400 and out.json()["code"] == "VISIT_DATE_OUT_OF_RANGE"
    short = client.post("/api/itinerary/calculate", json={**base, "start_time": "10:00", "end_time": "11:00"})
    assert short.json()["code"] == "TIME_TOO_SHORT"
    assert client.post("/api/itinerary/calculate", json={**base, "start_time": "25:00"}).status_code == 422
