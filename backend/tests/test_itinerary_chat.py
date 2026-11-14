"""AI 채팅의 일정 경로 — Groq(값 추출)·TourAPI·카카오는 가짜"""

from datetime import datetime, timedelta

import pytest

from app.agent import itinerary_chat, loop
from app.core.config import settings
from app.models.festival import Festival
from app.services import itinerary_service
from app.services.festival_service import today_kst


def place(cid, category, dlng):
    return {"content_id": cid, "name": f"{cid}집", "category": category, "address": None,
            "lng": 126.978 + dlng, "lat": 37.566, "image_url": None, "distance_m": 100}


NEARBY = {"attraction": [place("A1", "attraction", 0.005), place("A2", "attraction", 0.007)],
          "restaurant": [place("R1", "restaurant", 0.01), place("R2", "restaurant", 0.02)],
          "cafe": [place("C1", "cafe", 0.015), place("C2", "cafe", 0.017)]}


@pytest.fixture
def setup(db, monkeypatch):
    t = today_kst()
    db.add(Festival(content_id="F", title="서울빛초롱축제", start_date=t, end_date=t + timedelta(days=10), area_code="1",
                    lng=126.978, lat=37.566, playtime="10:00~22:00", detail_synced_at=datetime.now()))
    db.commit()
    monkeypatch.setattr(itinerary_service, "find_places", lambda lng, lat, category: NEARBY[category])
    monkeypatch.setattr(settings, "KAKAO_REST_API_KEY", "")
    monkeypatch.setattr(loop, "chat", lambda *a, **k: (_ for _ in ()).throw(AssertionError("반복 처리로 가면 안 됨")))
    return t


def fake_extract(monkeypatch, **values):
    base = {"festival_name": None, "visit_date": None, "start_time": None, "end_time": None,
            "add_categories": [], "remove_names": []}
    seen = []

    def fake(messages, **kwargs):
        seen.append(messages)
        return {**base, **values}

    monkeypatch.setattr(itinerary_chat, "chat_json", fake)
    return seen


def types(body):
    return [b["type"] for b in body["blocks"]]


def test_asks_date_when_missing(client, setup, monkeypatch):
    fake_extract(monkeypatch, festival_name="빛초롱")
    body = client.post("/api/agent/chat", json={"message": "빛초롱축제 일정 짜줘"}).json()
    assert body["intent"] == "itinerary" and types(body) == ["text", "quick_replies"]
    assert "언제" in body["blocks"][0]["text"]
    assert "서울빛초롱축제" in body["blocks"][1]["options"][0]["message"]


def test_asks_festival_when_not_found(client, setup, monkeypatch):
    fake_extract(monkeypatch, festival_name="없는축제")
    body = client.post("/api/agent/chat", json={"message": "없는축제 일정 짜줘"}).json()
    assert "어떤 축제" in body["blocks"][0]["text"]


def test_creates_timeline(client, setup, monkeypatch):
    seen = fake_extract(monkeypatch, festival_name="빛초롱", visit_date=setup.isoformat())
    body = client.post("/api/agent/chat", json={"message": "빛초롱 내일 일정 짜줘"}).json()
    assert types(body) == ["text", "timeline", "quick_replies"]
    timeline = body["blocks"][1]
    assert timeline["savable"] is True and timeline["itinerary"]["festival_content_id"] == "F"
    assert "10:00~21:00로 잡았어요" in body["blocks"][0]["text"]  # 기본 시간 안내
    assert "오늘은" in seen[0][0]["content"]  # 날짜 계산용 오늘 날짜


def test_edit_existing_itinerary_adds_cafe(client, setup, monkeypatch):
    fake_extract(monkeypatch, festival_name="빛초롱", visit_date=setup.isoformat())
    first = client.post("/api/agent/chat", json={"message": "빛초롱 일정 짜줘"}).json()["blocks"][1]["itinerary"]
    cafes_before = sum(1 for i in first["items"] if i["category"] == "cafe")

    fake_extract(monkeypatch, add_categories=["cafe"], end_time="21:00")
    body = client.post("/api/agent/chat", json={"message": "카페 추가해줘", "context": {"itinerary": first}}).json()
    edited = body["blocks"][1]["itinerary"]
    assert sum(1 for i in edited["items"] if i["category"] == "cafe") == cafes_before + 1
    # 기존 장소는 유지 (시간 안에 들어가는 한)
    assert {i["content_id"] for i in first["items"]} <= {i["content_id"] for i in edited["items"]} | {"A2"}


def test_out_of_range_date_offers_dates(client, setup, monkeypatch):
    fake_extract(monkeypatch, festival_name="빛초롱", visit_date=(setup + timedelta(days=30)).isoformat())
    body = client.post("/api/agent/chat", json={"message": "빛초롱 다음달 일정 짜줘"}).json()
    assert "축제 기간" in body["blocks"][0]["text"] and types(body) == ["text", "quick_replies"]
