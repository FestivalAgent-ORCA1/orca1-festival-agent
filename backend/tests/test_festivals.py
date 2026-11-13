from datetime import timedelta

import pytest

from app.models.festival import Festival, FestivalTag
from app.services.festival_service import today_kst


@pytest.fixture
def festivals(db):
    t = today_kst()
    d = timedelta

    def add(cid, title, start, end, area, tags, address=None, image=None):
        f = Festival(
            content_id=cid, title=title, start_date=t + d(start), end_date=t + d(end),
            area_code=area, address=address, image_url=image, lng=126.97, lat=37.56,
        )
        f.tags = [FestivalTag(tag_code=c) for c in tags]
        db.add(f)

    add("1", "서울빛초롱축제", -2, 10, "1", ["night", "art"], "서울특별시 중구 청계천로",
        "http://tong.visitkorea.or.kr/a.jpg")
    add("2", "부산불꽃축제", 5, 6, "6", ["night", "music"], "부산광역시 수영구")
    add("3", "이천쌀문화축제", 20, 25, "31", ["food", "local"], "경기도 이천시")
    add("4", "지난축제", -30, -1, "1", ["night"], "서울특별시")
    add("5", "광화문 야경 걷기", 1, 3, "1", ["night", "art"], "서울특별시 종로구")
    db.commit()


def ids(res):
    return [f["content_id"] for f in res.json()["items"]]


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_meta(client):
    tags = client.get("/api/meta/tags").json()
    assert {"code": "music", "name": "음악·공연"} in tags and len(tags) == 12
    assert len(client.get("/api/meta/regions").json()) == 17
    assert client.get("/api/meta/age-groups").json()[-1]["code"] == "50s_plus"


def test_list_excludes_ended_and_sorts(client, festivals):
    res = client.get("/api/festivals")
    body = res.json()
    assert res.status_code == 200
    assert ids(res) == ["1", "5", "2", "3"]  # start_date 순, 종료(4) 제외
    assert body["total"] == 4 and body["page"] == 1 and body["size"] == 20
    first = body["items"][0]
    assert first["status"] == "ongoing" and first["area_name"] == "서울"
    assert first["tags"] == ["art", "night"] and first["is_liked"] is False
    assert first["image_url"] == "https://tong.visitkorea.or.kr/a.jpg"  # http → https


def test_filters(client, festivals):
    assert ids(client.get("/api/festivals?area_code=6,31")) == ["2", "3"]
    assert ids(client.get("/api/festivals?tags=food,music")) == ["2", "3"]
    assert ids(client.get("/api/festivals?status=ongoing")) == ["1"]
    assert ids(client.get("/api/festivals?status=upcoming")) == ["5", "2", "3"]
    assert ids(client.get("/api/festivals?sort=title")) == ["5", "2", "1", "3"]


def test_keyword_title_and_address_ignore_spaces(client, festivals):
    assert ids(client.get("/api/festivals", params={"keyword": "빛 초롱"})) == ["1"]
    assert ids(client.get("/api/festivals", params={"keyword": "이천시"})) == ["3"]
    assert ids(client.get("/api/festivals", params={"keyword": "100%"})) == []


def test_paging(client, festivals):
    res = client.get("/api/festivals?page=2&size=3")
    assert ids(res) == ["3"] and res.json()["total"] == 4


def test_validation_error_format(client, festivals):
    res = client.get("/api/festivals?size=51")
    assert res.status_code == 422 and res.json()["code"] == "VALIDATION_ERROR"
    res = client.get("/api/festivals?start_date=2026-12-10&end_date=2026-12-01")
    assert res.status_code == 400 and res.json()["code"] == "BAD_REQUEST"


def test_detail_and_404(client, festivals):
    body = client.get("/api/festivals/1").json()
    assert body["title"] == "서울빛초롱축제" and "overview" in body and body["fee"] is None
    res = client.get("/api/festivals/nope")
    assert res.status_code == 404
    assert res.json() == {"code": "FESTIVAL_NOT_FOUND", "message": "축제를 찾을 수 없어요."}


def test_similar(client, festivals):
    # 1(night, art, 서울) 기준: 5(태그 2개 겹침) → 2(1개). 종료된 4, 자기 자신 제외
    assert [f["content_id"] for f in client.get("/api/festivals/1/similar").json()] == ["5", "2"]
    assert client.get("/api/festivals/nope/similar").status_code == 404


def test_unknown_route_format(client):
    res = client.get("/api/nothing")
    assert res.status_code == 404 and res.json()["code"] == "NOT_FOUND"
