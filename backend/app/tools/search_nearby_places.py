"""Tool: search_nearby_places — 축제 주변 장소 (docs/tool-spec.md 3번)

TourAPI locationBasedList2, 거리순. 결과가 3개 미만이면 반경을 2배로 늘려 한 번 더 찾는다.
"""

import httpx

from app.tools import tourapi_client as tour

CONTENT_TYPES = {"attraction": 12, "restaurant": 39, "cafe": 39}
# 카페 분류 코드: 구 분류 cat3 A05020900(카페/전통찻집), 신 분류 lclsSystm2 FD05 (검증 필요 → tags.md 4번)
CAFE_CAT3 = {"A05020900"}
CAFE_LCLS2 = {"FD05"}
DEFAULT_RADIUS, MAX_RADIUS = 3000, 20000
FETCH_ROWS = 100  # 카페·음식점을 나눠 걸러내야 해서 넉넉히 받음


def _is_cafe(item: dict) -> bool:
    return item.get("cat3") in CAFE_CAT3 or (item.get("lclsSystm2") or "") in CAFE_LCLS2


def _to_place(item: dict, category: str) -> dict:
    distance = tour.to_float(item.get("dist"))
    return {
        "content_id": tour.text(item.get("contentid")),
        "name": tour.text(item.get("title")),
        "category": category,
        "address": " ".join(filter(None, [tour.text(item.get("addr1")), tour.text(item.get("addr2"))])) or None,
        "image_url": tour.text(item.get("firstimage")),
        "lng": tour.to_float(item.get("mapx")),
        "lat": tour.to_float(item.get("mapy")),
        "distance_m": round(distance) if distance is not None else None,
    }


def find_places(
    lng: float, lat: float, category: str, radius: int = DEFAULT_RADIUS,
    *, client: httpx.Client | None = None,
) -> list[dict]:
    """가까운 순 Place 목록 전체 (실패하면 TourApiError). API·Tool이 함께 사용"""
    if category not in CONTENT_TYPES:
        raise ValueError(f"알 수 없는 category: {category}")
    radius = max(1, min(radius, MAX_RADIUS))

    def search(r: int) -> list[dict]:
        items = tour.call(
            "locationBasedList2",
            {"mapX": lng, "mapY": lat, "radius": r, "contentTypeId": CONTENT_TYPES[category],
             "arrange": "E", "numOfRows": FETCH_ROWS},
            client=client,
        )["items"]
        if category == "cafe":
            items = [i for i in items if _is_cafe(i)]
        elif category == "restaurant":
            items = [i for i in items if not _is_cafe(i)]
        return [_to_place(i, category) for i in items if tour.text(i.get("contentid"))]

    places = search(radius)
    if len(places) < 3 and radius < MAX_RADIUS:
        places = search(min(radius * 2, MAX_RADIUS))
    return places


def search_nearby_places(lng: float, lat: float, category: str, radius: int = DEFAULT_RADIUS, limit: int = 10) -> dict:
    """AI Tool용: 실패해도 예외 대신 {"ok": False, "error": ...}"""
    try:
        places = find_places(lng, lat, category, radius)
    except tour.TourApiError as exc:
        return {"ok": False, "error": {"code": exc.code, "message": "주변 장소를 가져오지 못했어요."}}
    except ValueError as exc:
        return {"ok": False, "error": {"code": "BAD_REQUEST", "message": str(exc)}}
    return {"ok": True, "places": places[: max(1, min(limit, 50))]}
