# Tool 명세

> 담당: BE1 · 상태: **초안**
>
> 각 Tool이 **받는 값 · 돌려주는 값 · 실패 시 동작**을 정의합니다.
> AI에게 주는 Tool 설명서(`agent/tool_schemas.py`)는 이 문서를 기준으로 작성합니다.

## 공통 규칙

- Tool 함수는 `backend/app/tools/` 파일 하나에 함수 하나. 함수 이름 = 파일 이름 = AI에게 알려주는 Tool 이름
- 받는 값·돌려주는 값은 **dict (JSON으로 바꿀 수 있는 값만)**. 날짜는 `YYYY-MM-DD`, 시각은 `HH:MM`
- 돌려주는 데이터 모양은 [api-spec.md](api-spec.md)의 FestivalSummary, Place, Itinerary와 같은 필드 이름을 사용
- **외부 API는 Tool 안에서만 호출** (`tourapi_client.py`, `kakao_client.py`를 통해서)
- 실패해도 예외를 AI 반복 처리 밖으로 던지지 않고, 아래 형식으로 돌려줌 → AI가 사용자에게 안내할 수 있게

```python
{"ok": False, "error": {"code": "TOURAPI_TIMEOUT", "message": "축제 정보를 가져오지 못했어요."}}
```

- 성공하면 `{"ok": True, ...결과}`
- AI에게 돌려주는 결과는 토큰을 아끼기 위해 **필요한 필드만** (예: overview는 200자로 자름)

---

## 외부 API 공통 호출

### `tourapi_client.py`

- 주소: `https://apis.data.go.kr/B551011/KorService2/{기능명}`
- 공통 파라미터: `serviceKey`(=`.env`의 `TOURAPI_SERVICE_KEY`), `MobileOS=ETC`, `MobileApp=FestivalAgent`, `_type=json`, `numOfRows`, `pageNo`
- 타임아웃 5초, 실패 시 1번 재시도
- 결과가 0건이면 `items`가 빈 문자열(`""`)로 오는 경우가 있음 → 빈 배열로 변환
- 결과가 1건이면 `item`이 배열이 아니라 객체로 오는 경우가 있음 → 항상 배열로 변환
- ⚠️ 개발 계정은 기능별 **하루 호출 수 제한**이 있음 → 개발 중 반복 테스트는 DB(동기화 데이터)로

### `kakao_client.py`

- 주소: `https://apis-navi.kakaomobility.com/v1/directions?origin={lng},{lat}&destination={lng},{lat}`
- 헤더: `Authorization: KakaoAK {KAKAO_REST_API_KEY}`
- 결과: `routes[0].summary.duration`(초), `routes[0].summary.distance`(미터)
- `routes[0].result_code`가 0이 아니면 (길 없음, 너무 가까움 등) 실패로 처리

---

## 1. `search_festivals` — 기간·지역으로 축제 찾기

| 받는 값 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `start_date` | str | O | 이 날짜 이후에 끝나는 축제 |
| `end_date` | str | X | 이 날짜 이전에 시작하는 축제 (기본: start_date + 30일) |
| `area_codes` | list[str] | X | [tags.md](tags.md) 지역 코드 |
| `tags` | list[str] | X | 태그 코드 (하나라도 겹치면 포함) |
| `keyword` | str | X | 축제명 일부 |
| `limit` | int | X | 기본 20, 최대 50 |

```python
{"ok": True, "festivals": [FestivalSummary, ...], "total": 34}
```

- 1주차: TourAPI `searchFestival2` 직접 호출 → 3주차 동기화 작업 이후: **우리 DB `festivals` 조회**로 변경 (받는 값·돌려주는 값은 그대로)
- AI가 "이번 주말" 같은 표현을 날짜로 바꿀 수 있도록 AI 지시문에 오늘 날짜·요일을 넣어줌 (`prompts.py`)

## 2. `get_festival_detail` — 축제 1개 상세

| 받는 값 | 타입 | 필수 |
| --- | --- | --- |
| `content_id` | str | O |

```python
{"ok": True, "festival": FestivalDetail}
```

- 우리 DB에 상세가 있고 7일 이내에 받은 것이면 DB 사용, 아니면 TourAPI `detailCommon2` + `detailIntro2`(contentTypeId=15) 호출 후 DB 갱신
- 없는 축제면 `{"ok": False, "error": {"code": "FESTIVAL_NOT_FOUND", ...}}`

## 3. `search_nearby_places` — 축제 주변 장소

| 받는 값 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `lng`, `lat` | float | O | 기준 좌표 (보통 축제 좌표) |
| `category` | str | O | `attraction` / `restaurant` / `cafe` |
| `radius` | int | X | 미터, 기본 3000, 최대 20000 |
| `limit` | int | X | 기본 10 |

```python
{"ok": True, "places": [Place, ...]}   # 가까운 순
```

- TourAPI `locationBasedList2` (`mapX`, `mapY`, `radius`, `contentTypeId`, `arrange=E`(거리순))
- `category` ↔ `contentTypeId` 대응은 [tags.md](tags.md) 4번 참고
- 결과가 너무 적으면(3개 미만) 반경을 2배로 늘려 한 번 더 찾기

## 4. `calc_travel_time` — 두 장소 사이 이동 시간 (자동차)

| 받는 값 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `legs` | list | O | `[{"from": {"content_id", "lng", "lat"}, "to": {...}}, ...]` 이웃한 장소 쌍 목록 |

```python
{
  "ok": True,
  "legs": [
    {"from_content_id": "126508", "to_content_id": "2871024",
     "duration_min": 15, "distance_km": 2.3, "source": "cache"}
  ]
}
```

- `source`: `cache`(DB `travel_times`) / `kakao`(새로 계산) / `estimate`(카카오 실패 시 직선거리로 추정)
- 순서: DB 캐시 확인 → 없으면 카카오 호출 → 결과를 DB에 저장
- 카카오 실패 시 추정값: 직선거리 × 1.4 ÷ 시속 30km, 최소 5분. 이때 `warnings`에 표시되도록 `source="estimate"`
- **모든 조합을 계산하지 않음**. 방문 순서상 이웃한 쌍만 (장소 N개 → N-1번)

## 5. `score_festivals` — 추천 점수 (계산만)

| 받는 값 | 타입 | 설명 |
| --- | --- | --- |
| `festivals` | list[FestivalSummary] | 후보 축제 |
| `profile` | dict | `get_profile()` 결과: `age_group`, `regions`, `tags` |
| `liked_ids` | list[str] | `list_liked_ids()` 결과 |
| `today` | str | 기준 날짜 |

```python
{"ok": True, "festivals": [{**FestivalSummary, "score": 87, "score_detail": {"tag": 40, "region": 25, "liked": 10, "date": 12}}]}
```

점수(100점 만점, 초안 — 테스트하며 조정):

| 항목 | 배점 | 계산 |
| --- | --- | --- |
| 관심사 일치 | 40 | 사용자 태그와 겹치는 축제 태그 수 ÷ 축제 태그 수 × 40 |
| 선호 지역 | 25 | 선호 지역이면 25, 선호 지역이 없으면(전국) 모두 12 |
| 찜 유사도 | 20 | 찜한 축제들과 태그가 겹치는 정도 (찜이 없으면 모두 10) |
| 날짜 | 15 | 진행 중 15, 7일 이내 시작 12, 30일 이내 8, 그 이후 3 |

- 이미 찜한 축제, 종료된 축제는 후보에서 제외
- 추천 이유(`reason`) 문장은 이 Tool이 아니라 AI가 `score_detail`을 보고 작성

## 6. `build_timeline` — 방문 순서와 시간표 (계산만)

| 받는 값 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `festival` | FestivalDetail | O | |
| `places` | list[Place] | O | 넣을 장소 (축제 제외) |
| `visit_date` | str | O | |
| `start_time`, `end_time` | str | O | |
| `travel_legs` | list | X | `calc_travel_time` 결과. 없으면 직선거리로 추정해서 배치 |

```python
{"ok": True, "itinerary": Itinerary}
```

배치 규칙 (초안):

- 머무는 시간 기본값: 축제 120분, 관광지 60분, 음식점 60분, 카페 40분
- 점심 11:30~13:30, 저녁 17:30~19:30 사이에 음식점 1곳씩 (일정 시간에 해당 구간이 있을 때만)
- 축제 `playtime`을 읽을 수 있으면 운영 시간 안에 축제를 배치. 야간 축제(시작 17시 이후)는 저녁 이후로
- 나머지 장소 순서: 직전 장소에서 가장 가까운 곳부터 (nearest neighbor)
- 장소 사이에는 이동 시간 + 여유 5분을 두고, 시작 시각은 5분 단위로 올림

## 7. `validate_schedule` — 시간표 검사 (계산만)

| 받는 값 | 타입 | 필수 |
| --- | --- | --- |
| `itinerary` | Itinerary | O |
| `festival` | FestivalDetail | O |

```python
{
  "ok": True,
  "valid": False,
  "errors":   [{"code": "VISIT_DATE_OUT_OF_RANGE", "message": "...", "seq": None}],
  "warnings": [{"code": "LONG_TRAVEL", "message": "경복궁 → 토속촌 이동이 60분 넘게 걸려요.", "seq": 2}]
}
```

| 구분 | code | 검사 내용 |
| --- | --- | --- |
| error | `VISIT_DATE_OUT_OF_RANGE` | 방문일이 축제 기간 밖 |
| error | `TIME_OVERLAP` | 장소끼리 시간이 겹침 |
| error | `EXCEEDS_END_TIME` | 마지막 장소가 종료 시각을 넘김 |
| error | `FESTIVAL_MISSING` | 시간표에 축제가 없음 |
| warning | `FESTIVAL_TIME_UNKNOWN` | 운영 시간 정보가 없어 가정한 시간 사용 |
| warning | `OUTSIDE_PLAYTIME` | 축제 운영 시간 밖에 배치됨 |
| warning | `LONG_TRAVEL` | 한 구간 이동 60분 초과 |
| warning | `NO_MEAL` | 식사 시간대가 있는데 음식점 없음 |
| warning | `TRAVEL_ESTIMATED` | 일부 이동 시간이 추정값 |

- `errors`가 있으면 `valid=False` → 서비스가 장소를 빼거나 다시 배치 (최대 2회), 그래도 안 되면 사용자에게 안내
- `warnings`는 그대로 Itinerary의 `warnings`로 전달

---

## Tool이 아닌 내부 함수 (서비스 계층)

AI가 직접 고르지 않고, 서비스·배치에서 호출하는 함수입니다.

| 함수 | 담당 | 위치 | 하는 일 |
| --- | --- | --- | --- |
| `get_profile(user_id)` | BE2 | `services/user_service.py` | `{"age_group", "regions", "tags"}` 반환. 비로그인·미설정이면 `None` |
| `list_liked_ids(user_id)` | BE2 | `services/like_service.py` | 찜한 축제 `content_id` 목록 |
| `get_festival(content_id)` | BE1 | `services/festival_service.py` | DB에서 축제 1개 (FestivalDetail) |
| `similar_festivals(content_id, limit)` | BE1 | `services/festival_service.py` | 태그·지역이 비슷한 진행 예정 축제. 찜 알림·상세 페이지에서 사용 |
