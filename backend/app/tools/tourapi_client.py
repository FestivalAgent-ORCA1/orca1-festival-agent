"""TourAPI(KorService2) 공통 호출 (docs/tool-spec.md '외부 API 공통 호출')

- 키는 공공데이터포털의 **Decoding(일반 인증키)** 값을 .env TOURAPI_SERVICE_KEY에 넣는다
  (httpx가 주소에 넣을 때 알아서 인코딩하므로, Encoding 키를 넣으면 두 번 인코딩되어 실패)
- 개발 계정은 기능별 하루 호출 수 제한이 있다 → 반복 테스트는 DB(동기화 데이터)로
"""

import re
from datetime import date, datetime
from html import unescape

import httpx

from app.core.config import settings

BASE_URL = "https://apis.data.go.kr/B551011/KorService2"
TIMEOUT = 5.0
RETRY = 1

# 법정동 시·도 코드(lDongRegnCd) → 우리 지역 코드(tags.md)
# 2026-11-11 실제 응답 확인: searchFestival2의 areacode는 **항상 비어 있음** → 이 표로 지역을 정함
# 세종은 "36110"으로 와서 앞 2자리("36")로 찾는다. 29(광주)·46(전남)·42·45는 옛 코드 (혹시 올 때 대비)
LDONG_TO_AREA = {
    "11": "1", "28": "2", "30": "3", "27": "4", "29": "5", "26": "6", "31": "7", "36": "8",
    "41": "31", "42": "32", "51": "32", "43": "33", "44": "34", "47": "35", "48": "36",
    "45": "37", "52": "37", "46": "38", "50": "39",
}
# "12" = 전남광주통합특별시 (ldongCode2로 확인). 옛 광주 5개 구만 광주(5), 나머지 시·군은 전남(38)
LDONG_UNIFIED_GWANGJU_JEONNAM = "12"
GWANGJU_SIGNGU = {"210", "240", "270", "300", "330"}  # 동구·서구·남구·북구·광산구


class TourApiError(Exception):
    def __init__(self, code: str, message: str = "관광 정보를 가져오지 못했어요."):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def call(operation: str, params: dict | None = None, *, client: httpx.Client | None = None) -> dict:
    """TourAPI 호출 → {"items": [...], "total": n}. 실패하면 TourApiError"""
    if not settings.TOURAPI_SERVICE_KEY:
        raise TourApiError("TOURAPI_KEY_MISSING", "TourAPI 키가 설정되지 않았어요.")
    query = {
        "serviceKey": settings.TOURAPI_SERVICE_KEY,
        "MobileOS": "ETC",
        "MobileApp": "FestivalAgent",
        "_type": "json",
        "numOfRows": 100,
        "pageNo": 1,
        **{k: v for k, v in (params or {}).items() if v is not None and v != ""},
    }
    owns_client = client is None
    client = client or httpx.Client(timeout=TIMEOUT)
    try:
        last_error: TourApiError | None = None
        for _ in range(RETRY + 1):
            try:
                response = client.get(f"{BASE_URL}/{operation}", params=query)
                response.raise_for_status()
                return _parse(response)
            except httpx.TimeoutException:
                last_error = TourApiError("TOURAPI_TIMEOUT")
            except httpx.HTTPError as exc:
                last_error = TourApiError("TOURAPI_HTTP_ERROR", f"관광 정보를 가져오지 못했어요. ({exc})")
            except TourApiError as exc:
                # 키·파라미터 오류는 다시 해도 같으므로 바로 실패
                raise exc
        raise last_error  # type: ignore[misc]
    finally:
        if owns_client:
            client.close()


def _parse(response: httpx.Response) -> dict:
    try:
        data = response.json()
    except ValueError:
        # 키 오류 등은 _type=json이어도 XML로 온다
        reason = re.search(r"<returnAuthMsg>(.*?)</returnAuthMsg>", response.text)
        raise TourApiError("TOURAPI_BAD_RESPONSE", reason.group(1) if reason else "응답 형식이 올바르지 않아요.")

    body_root = data.get("response", data)
    header = body_root.get("header", {})
    if header.get("resultCode") not in (None, "0000", "00"):
        raise TourApiError(f"TOURAPI_{header.get('resultCode')}", header.get("resultMsg") or "TourAPI 오류")
    body = body_root.get("body") or {}
    items = body.get("items")
    if not items:  # 0건이면 "" 로 오는 경우
        item_list = []
    else:
        item = items.get("item", [])
        item_list = item if isinstance(item, list) else [item]  # 1건이면 객체로 오는 경우
    return {"items": item_list, "total": int(body.get("totalCount") or 0)}


# ---- 값 변환 ----


def parse_date(value: str | None) -> date | None:
    """YYYYMMDD → date"""
    try:
        return datetime.strptime((value or "").strip(), "%Y%m%d").date()
    except ValueError:
        return None


def parse_datetime(value: str | None) -> datetime | None:
    """YYYYMMDDhhmmss → datetime"""
    try:
        return datetime.strptime((value or "").strip(), "%Y%m%d%H%M%S")
    except ValueError:
        return None


def to_float(value) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number or None  # 좌표 0은 값이 없는 것으로 봄


def text(value) -> str | None:
    """빈 문자열은 None"""
    value = (str(value) if value is not None else "").strip()
    return value or None


def clean_html(value: str | None) -> str | None:
    """<br> → 줄바꿈, 나머지 태그 제거, &amp; 등 변환"""
    if not value:
        return None
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.I)
    value = unescape(re.sub(r"<[^>]+>", "", value))
    return value.strip() or None


def extract_url(value: str | None) -> str | None:
    """homepage는 <a href="...">...</a> 형태로 와서 첫 주소만 꺼냄"""
    if not value:
        return None
    match = re.search(r"href=[\"']([^\"']+)[\"']", value) or re.search(r"https?://[^\s<\"']+", value)
    return unescape(match.group(1) if match.re.groups else match.group(0)) if match else None


def area_code_of(item: dict) -> str | None:
    if code := text(item.get("areacode")):
        return code
    ldong = text(item.get("lDongRegnCd"))
    if not ldong:
        return None
    if ldong == LDONG_UNIFIED_GWANGJU_JEONNAM:
        return "5" if text(item.get("lDongSignguCd")) in GWANGJU_SIGNGU else "38"
    return LDONG_TO_AREA.get(ldong[:2])
