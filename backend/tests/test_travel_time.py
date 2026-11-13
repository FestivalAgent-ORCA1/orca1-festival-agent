"""이동 시간 계산 — 카카오는 가짜 응답으로 확인"""

from datetime import timedelta

import httpx
import pytest

from app.core.config import settings
from app.models.festival import TravelTime
from app.tools import calc_travel_time as module
from app.tools.calc_travel_time import calc_travel_time, compute_legs

A = {"content_id": "a", "lng": 126.9769, "lat": 37.5796}  # 경복궁
B = {"content_id": "b", "lng": 126.9707, "lat": 37.5779}  # 1km 정도 떨어진 곳


@pytest.fixture(autouse=True)
def fake_key(monkeypatch):
    monkeypatch.setattr(settings, "KAKAO_REST_API_KEY", "test-key")


def kakao(result_code=0, duration=232, distance=1108, status=200):
    calls = []

    def handler(request):
        calls.append(request)
        body = {"routes": [{"result_code": result_code, "result_msg": "msg",
                            "summary": {"duration": duration, "distance": distance}}]}
        return httpx.Response(status, json=body)

    return httpx.Client(transport=httpx.MockTransport(handler)), calls


def test_kakao_then_cache(db):
    client, calls = kakao()
    first = compute_legs(db, [{"from": A, "to": B}], client=client)
    assert first == [{"from_content_id": "a", "to_content_id": "b", "duration_min": 4, "distance_km": 1.11, "source": "kakao"}]
    assert calls[0].headers["Authorization"] == "KakaoAK test-key"
    assert calls[0].url.params["origin"] == "126.9769,37.5796"

    second = compute_legs(db, [{"from": A, "to": B}], client=client)
    assert second[0]["source"] == "cache" and len(calls) == 1
    # 방향이 있음: 반대 방향은 다시 계산
    assert compute_legs(db, [{"from": B, "to": A}], client=client)[0]["source"] == "kakao"


def test_expired_cache_recalculated(db):
    client, calls = kakao()
    compute_legs(db, [{"from": A, "to": B}], client=client)
    row = db.get(TravelTime, ("a", "b"))
    row.created_at = row.created_at - timedelta(days=module.CACHE_DAYS + 1)
    db.commit()
    assert compute_legs(db, [{"from": A, "to": B}], client=client)[0]["source"] == "kakao"
    assert len(calls) == 2


def test_estimate_when_kakao_fails(db):
    client, _ = kakao(result_code=104)
    leg = compute_legs(db, [{"from": A, "to": B}], client=client)[0]
    assert leg["source"] == "estimate" and leg["duration_min"] >= module.MIN_ESTIMATE_MIN
    assert db.get(TravelTime, ("a", "b")) is None  # 추정값은 저장하지 않음


def test_same_or_very_near_place(db):
    client, calls = kakao()
    near = {"content_id": "n", "lng": A["lng"] + 0.0001, "lat": A["lat"]}
    legs = compute_legs(db, [{"from": A, "to": A}, {"from": A, "to": near}], client=client)
    assert [l["source"] for l in legs] == ["cache", "estimate"] and not calls


def test_tool_bad_input(db):
    assert calc_travel_time([{"from": {"content_id": "a"}, "to": B}], db=db)["error"]["code"] == "BAD_REQUEST"
