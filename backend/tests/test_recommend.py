"""추천 점수·맞춤 추천 API — AI(추천 이유)는 가짜로"""

from datetime import date, timedelta

import pytest

from app.agent.client import AiError
from app.models.festival import Festival, FestivalTag
from app.services import recommend_service
from app.services.festival_service import today_kst
from app.tools.score_festivals import score_festivals

TODAY = date(2026, 11, 11)


def f(cid, tags, area, start_days, end_days=None):
    return {"content_id": cid, "tags": tags, "area_code": area,
            "start_date": (TODAY + timedelta(start_days)).isoformat(),
            "end_date": (TODAY + timedelta(end_days if end_days is not None else start_days + 2)).isoformat()}


def test_score_rules():
    profile = {"tags": ["food", "night"], "regions": ["1"]}
    result = score_festivals(
        [f("a", ["food"], "1", 0), f("b", ["music", "art"], "6", 40), f("old", ["food"], "1", -5, -1), f("liked", ["food"], "1", 0)],
        profile, liked_ids=["liked"], today=TODAY, liked_tags={"food"},
    )["festivals"]
    assert [x["content_id"] for x in result] == ["a", "b"]  # 종료·찜한 축제 제외, 점수 높은 순
    assert result[0]["score_detail"] == {"tag": 40, "region": 25, "liked": 20, "date": 15}
    assert result[1]["score_detail"] == {"tag": 0, "region": 0, "liked": 0, "date": 3}


def test_score_defaults_without_regions_or_likes():
    s = score_festivals([f("a", ["food", "music"], "1", 5)], {"tags": ["food"], "regions": []}, today=TODAY)["festivals"][0]
    assert s["score_detail"] == {"tag": 20, "region": 12, "liked": 10, "date": 12}


@pytest.fixture
def user_headers(client):
    token = client.post("/api/auth/signup", json={"email": "r@example.com", "password": "password123", "nickname": "추천"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def add(db, cid, title, tags, area, start_days=0):
    t = today_kst()
    fest = Festival(content_id=cid, title=title, start_date=t + timedelta(start_days), end_date=t + timedelta(start_days + 3), area_code=area)
    fest.tags = [FestivalTag(tag_code=x) for x in tags]
    db.add(fest)
    db.commit()


def test_recommended_requires_onboarding(client, user_headers):
    assert client.get("/api/festivals/recommended").status_code == 401
    res = client.get("/api/festivals/recommended", headers=user_headers)
    assert res.status_code == 400 and res.json()["code"] == "ONBOARDING_REQUIRED"


def test_recommended_with_ai_reasons(client, db, user_headers, monkeypatch):
    client.put("/api/users/me/preferences", headers=user_headers, json={"age_group": "20s", "regions": ["1"], "tags": ["food"]})
    add(db, "1", "서울 음식 축제", ["food"], "1")
    add(db, "2", "부산 음악 축제", ["music"], "6", 20)
    monkeypatch.setattr(recommend_service, "chat_json", lambda *a, **k: {"reasons": {"1": "좋아하시는 음식 축제예요."}})
    body = client.get("/api/festivals/recommended", headers=user_headers).json()
    assert [x["content_id"] for x in body] == ["1", "2"]
    assert body[0]["reason"] == "좋아하시는 음식 축제예요." and body[0]["score"] == 90
    assert body[1]["reason"]  # AI가 빠뜨린 축제는 기본 문장
    assert "score_detail" not in body[0]


def test_recommended_falls_back_when_ai_fails(client, db, user_headers, monkeypatch):
    client.put("/api/users/me/preferences", headers=user_headers, json={"age_group": "20s", "regions": ["1"], "tags": ["food"]})
    add(db, "1", "서울 음식 축제", ["food"], "1")

    def fail(*a, **k):
        raise AiError("AI_RATE_LIMITED")

    monkeypatch.setattr(recommend_service, "chat_json", fail)
    res = client.get("/api/festivals/recommended", headers=user_headers)
    assert res.status_code == 200
    assert res.json()[0]["reason"] == "좋아하시는 음식·먹거리 축제예요, 선호 지역인 서울에서 열려요, 지금 진행 중이에요."
