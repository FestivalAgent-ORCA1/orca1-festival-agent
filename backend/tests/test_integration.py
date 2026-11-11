"""BE1(축제)과 BE2(회원·찜·일정·커뮤니티·알림) API가 한 서버에서 같이 동작하는지 확인"""

from datetime import timedelta

import pytest

from app.models.festival import Festival, FestivalTag
from app.services.festival_service import today_kst


@pytest.fixture
def festival(db):
    t = today_kst()
    f = Festival(
        content_id="100", title="서울빛초롱축제", start_date=t, end_date=t + timedelta(days=5),
        area_code="1", address="서울특별시 중구",
    )
    f.tags = [FestivalTag(tag_code="night")]
    db.add(f)
    db.commit()
    return f


@pytest.fixture
def auth(client):
    res = client.post(
        "/api/auth/signup",
        json={"email": "a@example.com", "password": "password123", "nickname": "축제러버"},
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["user"]["onboarded"] is False
    return {"Authorization": f"Bearer {body['access_token']}"}


def test_login_and_me(client, auth):
    res = client.post("/api/auth/login", json={"email": "a@example.com", "password": "password123"})
    assert res.status_code == 200
    assert client.get("/api/users/me", headers=auth).json()["nickname"] == "축제러버"
    assert client.get("/api/users/me").json()["code"] == "UNAUTHORIZED"
    bad = client.post("/api/auth/login", json={"email": "a@example.com", "password": "wrong-pass"})
    assert bad.status_code == 401 and bad.json()["code"] == "INVALID_CREDENTIALS"


def test_preferences(client, auth):
    res = client.put(
        "/api/users/me/preferences", headers=auth,
        json={"age_group": "20s", "regions": ["1", "31"], "tags": ["music", "food"]},
    )
    assert res.status_code == 200 and res.json()["onboarded"] is True


def test_like_sets_is_liked_on_festival_api(client, auth, festival):
    assert client.get("/api/festivals/100", headers=auth).json()["is_liked"] is False
    assert client.post("/api/likes", headers=auth, json={"content_id": "100"}).status_code == 201
    dup = client.post("/api/likes", headers=auth, json={"content_id": "100"})
    assert dup.status_code == 409 and dup.json()["code"] == "ALREADY_LIKED"

    assert client.get("/api/festivals/100", headers=auth).json()["is_liked"] is True
    assert client.get("/api/festivals", headers=auth).json()["items"][0]["is_liked"] is True
    assert client.get("/api/festivals/100").json()["is_liked"] is False  # 로그인 안 하면 false

    likes = client.get("/api/likes", headers=auth).json()
    assert likes["total"] == 1 and likes["items"][0]["content_id"] == "100"

    assert client.delete("/api/likes/100", headers=auth).status_code == 204
    assert client.get("/api/festivals/100", headers=auth).json()["is_liked"] is False


def test_expired_token_on_optional_api_is_ignored(client, festival):
    res = client.get("/api/festivals", headers={"Authorization": "Bearer broken"})
    assert res.status_code == 200


def test_schedule_crud(client, auth, festival):
    body = {
        "title": "빛초롱 데이트", "festival_content_id": "100",
        "visit_date": str(today_kst()), "start_time": "10:00", "end_time": "21:00",
        "total_travel_min": 15,
        "items": [{
            "seq": 1, "category": "festival", "content_id": "100", "name": "서울빛초롱축제",
            "start_time": "17:00", "end_time": "19:00",
        }],
    }
    res = client.post("/api/schedules", headers=auth, json=body)
    assert res.status_code == 201, res.text
    sid = res.json()["id"]
    assert res.json()["start_time"] == "10:00"
    assert client.get(f"/api/schedules/{sid}", headers=auth).status_code == 200
    assert client.get("/api/schedules", headers=auth).json()["total"] == 1
    assert client.delete(f"/api/schedules/{sid}", headers=auth).status_code == 204


def test_posts_and_comments(client, auth, festival):
    res = client.post(
        "/api/posts", headers=auth,
        json={"title": "다녀왔어요", "content": "좋았어요", "festival_content_id": "100"},
    )
    assert res.status_code == 201, res.text
    pid = res.json()["id"]
    assert client.get("/api/posts").json()["total"] == 1
    assert client.post(f"/api/posts/{pid}/comments", headers=auth, json={"content": "부러워요"}).status_code == 201
    assert len(client.get(f"/api/posts/{pid}/comments").json()) == 1


def test_notifications_empty(client, auth):
    assert client.get("/api/notifications", headers=auth).json()["total"] == 0
    assert client.get("/api/notifications/unread-count", headers=auth).json() == {"count": 0}
