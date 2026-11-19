"""Tool: search_nearby_places — 축제 주변 장소 (docs/tool-spec.md 3번)

TourAPI locationBasedList2, 거리순. 결과가 3개 미만이면 반경을 2배로 늘려 한 번 더 찾는다.
체험 프로그램을 운영하는 회사가 관광지로 등록된 경우가 있어 이름으로 걸러낸다 (_clean_name).
"""

import re

import httpx

from app.tools import tourapi_client as tour

CONTENT_TYPES = {"attraction": 12, "restaurant": 39, "cafe": 39}
# 카페 분류 코드: 구 분류 cat3 A05020900(카페/전통찻집), 신 분류 lclsSystm2 FD05 (검증 필요 → tags.md 4번)
CAFE_CAT3 = {"A05020900"}
CAFE_LCLS2 = {"FD05"}
DEFAULT_RADIUS, MAX_RADIUS = 3000, 20000
FETCH_ROWS = 100  # 카페·음식점을 나눠 걸러내야 해서 넉넉히 받음

# 2026-11-19 확인: 축제 23곳 주변 관광지 95개 중 6개가 회사 이름 (모두 체험관광 EX, 사진 없음)
#   '주식회사뷰티홀릭', '컬러브릿지협동조합' → 이름이 회사명뿐이라 뺌
#   '수달궁(문화살롱주식회사)' → 실제 장소라 괄호(운영 회사)만 떼고 '수달궁'으로
COMPANY_WORDS = re.compile(r"주식회사|유한회사|\(주\)|㈜|협동조합|조합법인|회사법인")
TRAILING_PAREN = re.compile(r"\s*\(([^()]*)\)\s*$")


def _clean_name(title: str | None) -> str | None:
    """장소 이름에서 운영 회사 표기를 뗀다. 이름이 회사명뿐이면 None (목록에서 뺌)"""
    name = (title or "").strip()
    paren = TRAILING_PAREN.search(name)
    if paren and (paren.group(1).strip() == "주" or COMPANY_WORDS.search(paren.group(1))):
        name = name[: paren.start()].strip()
    if not name or COMPANY_WORDS.search(name):
        return None
    return name


def _is_cafe(item: dict) -> bool:
    return item.get("cat3") in CAFE_CAT3 or (item.get("lclsSystm2") or "") in CAFE_LCLS2


def _to_place(item: dict, category: str, name: str) -> dict:
    distance = tour.to_float(item.get("dist"))
    return {
        "content_id": tour.text(item.get("contentid")),
        "name": name,
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
        places = []
        for item in items:
            name = _clean_name(tour.text(item.get("title")))
            if name and tour.text(item.get("contentid")):
                places.append(_to_place(item, category, name))
        return places

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
