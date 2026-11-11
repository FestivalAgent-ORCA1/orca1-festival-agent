"""카카오모빌리티 자동차 길찾기 (docs/tool-spec.md 'kakao_client.py')

- 키: .env KAKAO_REST_API_KEY (카카오 개발자 앱의 REST API 키). 2026-11-11 실제 호출 확인 (별도 권한 신청 불필요)
- 무료 사용량 하루 약 1만 건 → 결과는 travel_times에 캐시해서 다시 씀 (calc_travel_time.py)
"""

import httpx

from app.core.config import settings

DIRECTIONS_URL = "https://apis-navi.kakaomobility.com/v1/directions"
TIMEOUT = 5.0
RETRY = 1


class KakaoError(Exception):
    def __init__(self, code: str, message: str = "이동 시간을 계산하지 못했어요."):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def directions(
    from_lng: float, from_lat: float, to_lng: float, to_lat: float, *, client: httpx.Client | None = None
) -> tuple[int, int]:
    """자동차 길찾기 → (걸리는 시간 초, 거리 미터). 실패하면 KakaoError"""
    if not settings.KAKAO_REST_API_KEY:
        raise KakaoError("KAKAO_KEY_MISSING", "카카오 키가 설정되지 않았어요.")
    params = {"origin": f"{from_lng},{from_lat}", "destination": f"{to_lng},{to_lat}"}
    headers = {"Authorization": f"KakaoAK {settings.KAKAO_REST_API_KEY}"}
    owns_client = client is None
    client = client or httpx.Client(timeout=TIMEOUT)
    try:
        last_error = KakaoError("KAKAO_ERROR")
        for _ in range(RETRY + 1):
            try:
                response = client.get(DIRECTIONS_URL, params=params, headers=headers)
            except httpx.TimeoutException:
                last_error = KakaoError("KAKAO_TIMEOUT")
                continue
            except httpx.HTTPError as exc:
                last_error = KakaoError("KAKAO_HTTP_ERROR", f"이동 시간을 계산하지 못했어요. ({exc})")
                continue
            if response.status_code in (401, 403):
                raise KakaoError("KAKAO_AUTH_ERROR", "카카오 키 또는 사용 권한을 확인해 주세요.")
            if response.status_code >= 500:
                last_error = KakaoError("KAKAO_HTTP_ERROR", f"카카오 서버 오류 ({response.status_code})")
                continue
            return _parse(response)
        raise last_error
    finally:
        if owns_client:
            client.close()


def _parse(response: httpx.Response) -> tuple[int, int]:
    try:
        route = response.json()["routes"][0]
    except (ValueError, KeyError, IndexError, TypeError):
        raise KakaoError("KAKAO_BAD_RESPONSE", "길찾기 응답 형식이 올바르지 않아요.")
    if route.get("result_code") != 0:
        # 104: 출발지와 도착지가 5m 이내, 그 외: 길 없음 등
        raise KakaoError(f"KAKAO_ROUTE_{route.get('result_code')}", route.get("result_msg") or "경로를 찾지 못했어요.")
    summary = route.get("summary") or {}
    return int(summary.get("duration", 0)), int(summary.get("distance", 0))
