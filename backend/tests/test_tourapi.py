"""TourAPI 연결 — 실제로 호출하지 않고 가짜 응답으로 확인 (실제 응답 모양은 키 발급 후 검증 필요)"""

from datetime import date, timedelta

import httpx
import pytest

from app.batch.sync_festivals import sync_festivals
from app.core.config import settings
from app.models.festival import Festival
from app.services.festival_service import today_kst
from app.tools import tourapi_client as tour
from app.tools.search_nearby_places import search_nearby_places


@pytest.fixture(autouse=True)
def fake_key(monkeypatch):
    monkeypatch.setattr(settings, "TOURAPI_SERVICE_KEY", "test-key")


def wrap(items, total=None):
    body_items = "" if items == [] else {"item": items}
    return {"response": {"header": {"resultCode": "0000", "resultMsg": "OK"},
                         "body": {"items": body_items, "totalCount": len(items) if total is None else total}}}


def mock_client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_parse_empty_single_and_error():
    assert tour.call("x", client=mock_client(lambda r: httpx.Response(200, json=wrap([])))) == {"items": [], "total": 0}
    single = {"response": {"header": {"resultCode": "0000"}, "body": {"items": {"item": {"contentid": "1"}}, "totalCount": 1}}}
    assert tour.call("x", client=mock_client(lambda r: httpx.Response(200, json=single)))["items"] == [{"contentid": "1"}]

    xml = "<OpenAPI_ServiceResponse><returnAuthMsg>SERVICE_KEY_IS_NOT_REGISTERED_ERROR</returnAuthMsg></OpenAPI_ServiceResponse>"
    with pytest.raises(tour.TourApiError) as err:
        tour.call("x", client=mock_client(lambda r: httpx.Response(200, text=xml)))
    assert "SERVICE_KEY" in err.value.message


def test_retry_once_on_timeout():
    calls = []

    def handler(request):
        calls.append(1)
        if len(calls) == 1:
            raise httpx.ConnectTimeout("slow")
        return httpx.Response(200, json=wrap([{"contentid": "1"}]))

    assert tour.call("x", client=mock_client(handler))["total"] == 1 and len(calls) == 2


def test_value_helpers():
    assert tour.parse_date("20261101") == date(2026, 11, 1) and tour.parse_date("") is None
    assert tour.extract_url('<a href="https://a.com/x" target="_blank">a</a>') == "https://a.com/x"
    assert tour.extract_url("홈페이지 http://b.kr 참고") == "http://b.kr"
    assert tour.clean_html("17:00~<br>22:00 &amp; 무료") == "17:00~\n22:00 & 무료"
    assert tour.area_code_of({"areacode": "", "lDongRegnCd": "41"}) == "31"
    # 실제 응답 형태 (2026-11): 세종 36110, 전남광주통합특별시 12
    assert tour.area_code_of({"areacode": "", "lDongRegnCd": "36110"}) == "8"
    assert tour.area_code_of({"lDongRegnCd": "12", "lDongSignguCd": "300"}) == "5"  # 북구 → 광주
    assert tour.area_code_of({"lDongRegnCd": "12", "lDongSignguCd": "130"}) == "38"  # 여수시 → 전남
    assert tour.to_float("0") is None


def test_sync_festivals(db):
    t = today_kst()
    ymd = lambda d: d.strftime("%Y%m%d")  # noqa: E731
    festivals = [
        {"contentid": "10", "title": "빛초롱", "eventstartdate": ymd(t), "eventenddate": ymd(t + timedelta(5)),
         "areacode": "1", "addr1": "서울 중구", "mapx": "126.97", "mapy": "37.56",
         "firstimage": "http://img/a.jpg", "modifiedtime": "20261101120000"},
        {"contentid": "11", "title": "", "eventstartdate": ymd(t), "eventenddate": ymd(t)},  # 제목 없음 → 건너뜀
    ]
    seen = []

    def handler(request):
        op = request.url.path.rsplit("/", 1)[-1]
        seen.append(op)
        if op == "searchFestival2":
            return httpx.Response(200, json=wrap(festivals))
        if op == "detailCommon2":
            return httpx.Response(200, json=wrap([{"overview": "등 전시<br>야경", "homepage": '<a href="https://seoul.kr">홈</a>'}]))
        return httpx.Response(200, json=wrap([{"eventplace": "청계천", "playtime": "17:00~22:00", "usetimefestival": "무료"}]))

    stats = sync_festivals(db, client=mock_client(handler))
    assert stats["created"] == 1 and stats["detail_synced"] == 1
    f = db.get(Festival, "10")
    assert f.overview == "등 전시\n야경" and f.homepage == "https://seoul.kr" and f.fee == "무료"
    assert db.get(Festival, "11") is None

    # 다시 실행: modifiedtime이 같으면 상세는 다시 받지 않음
    seen.clear()
    stats = sync_festivals(db, client=mock_client(handler))
    assert stats["updated"] == 1 and stats["detail_synced"] == 0 and seen == ["searchFestival2"]


PLACES = [
    {"contentid": "p1", "title": "토속촌", "cat3": "A05020100", "dist": "120.5", "mapx": "126.9", "mapy": "37.5"},
    {"contentid": "p2", "title": "찻집", "cat3": "A05020900", "dist": "300"},
    {"contentid": "p3", "title": "국밥집", "cat3": "A05020100", "dist": "800"},
    {"contentid": "p4", "title": "냉면집", "cat3": "A05020100", "dist": "900"},
]


def test_nearby_tool_filters_cafe():
    def fake_call(operation, params, client=None):
        return {"items": PLACES, "total": 4}

    import app.tools.tourapi_client as module
    orig = module.call
    module.call = fake_call
    try:
        restaurants = search_nearby_places(126.9, 37.5, "restaurant")
        cafes = search_nearby_places(126.9, 37.5, "cafe")
    finally:
        module.call = orig
    assert [p["content_id"] for p in restaurants["places"]] == ["p1", "p3", "p4"]
    assert restaurants["places"][0]["distance_m"] == 120
    assert [p["name"] for p in cafes["places"]] == ["찻집"]


def test_nearby_api(client, db, monkeypatch):
    db.add(Festival(content_id="10", title="빛초롱", start_date=today_kst(), end_date=today_kst(), lng=126.9, lat=37.5))
    db.commit()
    monkeypatch.setattr(tour, "call", lambda op, params, client=None: {"items": PLACES, "total": 4})
    res = client.get("/api/places/nearby?content_id=10&category=restaurant&size=2")
    assert res.status_code == 200
    assert res.json()["total"] == 3 and [p["name"] for p in res.json()["items"]] == ["토속촌", "국밥집"]

    def fail(op, params, client=None):
        raise tour.TourApiError("TOURAPI_TIMEOUT")

    monkeypatch.setattr(tour, "call", fail)
    res = client.get("/api/places/nearby?content_id=10&category=cafe")
    assert res.status_code == 502 and res.json()["code"] == "EXTERNAL_API_ERROR"
    assert client.get("/api/places/nearby?content_id=nope&category=cafe").status_code == 404
