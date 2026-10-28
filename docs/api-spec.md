# API 명세

> 담당: BE1(축제·장소·일정 계산·메타·AI) · BE2(회원·찜·일정 저장·커뮤니티·알림) · 상태: **초안**
>
> API를 바꾸려면 **이 문서를 먼저 고치고** PR에 프론트 담당자를 리뷰어로 넣어주세요.
> 백엔드가 완성되기 전에는 프론트가 이 문서의 예시 응답으로 목업 데이터를 만들어 개발합니다.

## 0. 공통 규칙

### 주소와 형식

- 모든 주소는 `/api`로 시작
- 요청·응답 모두 JSON, 필드 이름은 **snake_case** (프론트에서도 변환하지 않고 그대로 사용)
- 개발 주소: 백엔드 `http://localhost:8000`, 프론트 `http://localhost:5173`
  - 프론트 `.env`의 `VITE_API_BASE_URL`에 백엔드 주소를 넣음
  - 백엔드는 CORS로 `http://localhost:5173`과 배포된 Vercel 주소를 허용
- 자동 문서: 백엔드 실행 후 `http://localhost:8000/docs` (FastAPI Swagger)

### 값 형식

| 종류 | 형식 | 예시 |
| --- | --- | --- |
| 날짜 | `YYYY-MM-DD` | `"2026-10-28"` |
| 시각 | `HH:MM` (24시간) | `"13:30"` |
| 날짜+시각 | ISO 8601, 한국 시간 | `"2026-10-28T09:00:00+09:00"` |
| 축제·장소 ID | 문자열 | `"2786391"` |
| 그 외 ID | 정수 | `12` |
| 좌표 | 숫자, `lng`(경도) / `lat`(위도) | `127.0276`, `37.4979` |
| 태그·지역·연령대 | [tags.md](tags.md)의 코드 | `"music"`, `"31"`, `"20s"` |

> TourAPI는 날짜를 `YYYYMMDD`로 주지만, 변환은 백엔드에서 하고 우리 API는 항상 `YYYY-MM-DD`를 씁니다.

### 로그인 (JWT)

- 로그인하면 `access_token`을 받음. 이후 요청 헤더에 `Authorization: Bearer <access_token>`
- 토큰 유효기간: 24시간. 만료·잘못된 토큰이면 `401` → 프론트(`api/client.js`)는 토큰을 지우고 `/login`으로 이동
- 아래 표에서 🔒 = 로그인 필수, 🔓 = 로그인 선택 (로그인하면 `is_liked` 같은 개인 정보가 채워짐), 표시 없음 = 누구나

### 목록 응답 (페이지네이션)

요청: `?page=1&size=20` (page는 1부터, size 최대 50)

```json
{
  "items": [],
  "page": 1,
  "size": 20,
  "total": 134
}
```

### 오류 응답

성공이 아닌 경우 아래 형식으로 돌려줍니다. 화면에는 `message`를 그대로 보여줘도 됩니다.

```json
{
  "code": "FESTIVAL_NOT_FOUND",
  "message": "축제를 찾을 수 없어요."
}
```

| HTTP | code 예시 | 상황 |
| --- | --- | --- |
| 400 | `BAD_REQUEST` | 값이 규칙에 맞지 않음 (예: 종료일이 시작일보다 빠름) |
| 401 | `UNAUTHORIZED` | 로그인 필요, 토큰 만료 |
| 403 | `FORBIDDEN` | 남의 글·일정 수정/삭제 |
| 404 | `*_NOT_FOUND` | 대상 없음 |
| 409 | `EMAIL_DUPLICATED`, `ALREADY_LIKED` | 중복 |
| 422 | `VALIDATION_ERROR` | 필수 값 누락, 타입 오류 (FastAPI 기본 422도 이 형식으로 바꿔서 응답) |
| 502 | `EXTERNAL_API_ERROR` | TourAPI·카카오·Groq 호출 실패 |
| 500 | `INTERNAL_ERROR` | 서버 오류 |

> BE2가 `main.py`에 공통 오류 처리기를 만들고, 각자 서비스에서는 공통 예외 클래스를 던지기만 합니다.

---

## 1. 공통 데이터 모양

여러 API에서 같은 모양을 씁니다. 필드를 추가할 때는 여기를 고치세요.

### FestivalSummary (축제 카드)

```json
{
  "content_id": "2786391",
  "title": "서울빛초롱축제",
  "start_date": "2026-11-01",
  "end_date": "2026-11-17",
  "status": "upcoming",
  "area_code": "1",
  "area_name": "서울",
  "address": "서울특별시 중구 청계천로 1",
  "image_url": "https://tong.visitkorea.or.kr/...jpg",
  "lng": 126.9779,
  "lat": 37.5690,
  "tags": ["night", "art"],
  "is_liked": false
}
```

- `status`: `upcoming`(예정) / `ongoing`(진행 중) / `ended`(종료) — 오늘 날짜 기준으로 백엔드가 계산
- `image_url`: 없으면 `null` → 프론트에서 기본 이미지
- `is_liked`: 로그인 안 했으면 항상 `false`

### FestivalDetail (축제 상세) = FestivalSummary + 아래 필드

```json
{
  "overview": "청계천을 따라 펼쳐지는 등 전시...",
  "place": "청계천 일대",
  "playtime": "17:00~22:00",
  "fee": "무료",
  "tel": "02-123-4567",
  "homepage": "https://..."
}
```

- `playtime`, `fee`는 TourAPI가 자유 형식 문자열로 주므로 그대로 보여줌. 없으면 `null`

### Place (주변 장소)

```json
{
  "content_id": "126508",
  "name": "경복궁",
  "category": "attraction",
  "address": "서울특별시 종로구 사직로 161",
  "image_url": null,
  "lng": 126.9770,
  "lat": 37.5796,
  "distance_m": 1200
}
```

- `category`: `attraction` / `restaurant` / `cafe`

### Itinerary (시간표)

일정 계산 결과, 저장된 일정 상세, AI 채팅의 timeline 블록에서 같은 모양을 씁니다.

```json
{
  "festival_content_id": "2786391",
  "visit_date": "2026-11-02",
  "start_time": "10:00",
  "end_time": "21:00",
  "total_travel_min": 55,
  "items": [
    {
      "seq": 1,
      "category": "attraction",
      "content_id": "126508",
      "name": "경복궁",
      "address": "서울특별시 종로구 사직로 161",
      "lng": 126.9770,
      "lat": 37.5796,
      "start_time": "10:00",
      "end_time": "11:30",
      "travel_min_from_prev": null,
      "distance_km_from_prev": null,
      "memo": null
    },
    {
      "seq": 2,
      "category": "restaurant",
      "content_id": "2871024",
      "name": "토속촌",
      "address": "...",
      "lng": 126.9707,
      "lat": 37.5779,
      "start_time": "11:45",
      "end_time": "12:45",
      "travel_min_from_prev": 15,
      "distance_km_from_prev": 2.3,
      "memo": null
    }
  ],
  "warnings": [
    { "code": "FESTIVAL_TIME_UNKNOWN", "message": "축제 운영 시간 정보가 없어 17시로 가정했어요." }
  ]
}
```

- `warnings`: `validate_schedule` 검사 결과 중 일정은 만들 수 있지만 알려야 할 내용. 없으면 `[]`

### User (내 정보)

```json
{
  "id": 3,
  "email": "user@example.com",
  "nickname": "축제러버",
  "age_group": "20s",
  "regions": ["1", "31"],
  "tags": ["music", "food"],
  "onboarded": true,
  "created_at": "2026-10-28T09:00:00+09:00"
}
```

---

## 2. 회원 · 로그인 (BE2 / FE3)

| 메서드 | 주소 | | 설명 |
| --- | --- | --- | --- |
| POST | `/api/auth/signup` | | 회원가입 |
| POST | `/api/auth/login` | | 로그인 |
| GET | `/api/users/me` | 🔒 | 내 정보 |
| PATCH | `/api/users/me` | 🔒 | 닉네임 수정 |
| PUT | `/api/users/me/preferences` | 🔒 | 첫 설정·관심사 수정 (연령대·지역·태그) |
| DELETE | `/api/users/me` | 🔒 | 탈퇴 |

**POST `/api/auth/signup`**

```json
// 요청
{ "email": "user@example.com", "password": "password123", "nickname": "축제러버" }
// 응답 201 — 가입과 동시에 로그인 처리
{ "access_token": "eyJ...", "token_type": "bearer", "user": { /* User, onboarded: false */ } }
```

- 비밀번호 8자 이상, 닉네임 2~15자. 이메일 중복이면 409 `EMAIL_DUPLICATED`

**POST `/api/auth/login`**

```json
// 요청
{ "email": "user@example.com", "password": "password123" }
// 응답 200
{ "access_token": "eyJ...", "token_type": "bearer", "user": { /* User */ } }
```

- 이메일·비밀번호 중 무엇이 틀렸는지 구분하지 않고 401 `INVALID_CREDENTIALS`
- 프론트: `user.onboarded === false`면 `/onboarding`으로 이동

**PUT `/api/users/me/preferences`**

```json
// 요청 (전체 교체)
{ "age_group": "20s", "regions": ["1", "31"], "tags": ["music", "food"] }
// 응답 200: User (onboarded: true로 바뀜)
```

- `regions` 0~3개, `tags` 1~5개. 목록에 없는 코드면 400

---

## 3. 메타 정보 (BE1 / FE1·FE3)

| 메서드 | 주소 | 설명 |
| --- | --- | --- |
| GET | `/api/meta/tags` | 관심사 태그 목록 |
| GET | `/api/meta/regions` | 지역 목록 |
| GET | `/api/meta/age-groups` | 연령대 목록 |

```json
// GET /api/meta/tags 응답
[ { "code": "music", "name": "음악·공연" }, { "code": "food", "name": "음식·먹거리" } ]
```

---

## 4. 축제 (BE1 / FE1)

| 메서드 | 주소 | | 설명 |
| --- | --- | --- | --- |
| GET | `/api/festivals` | 🔓 | 축제 목록 (검색·필터) |
| GET | `/api/festivals/recommended` | 🔒 | 맞춤 추천 (홈 화면) |
| GET | `/api/festivals/{content_id}` | 🔓 | 축제 상세 |
| GET | `/api/festivals/{content_id}/similar` | 🔓 | 비슷한 축제 |

**GET `/api/festivals`**

| 파라미터 | 예시 | 설명 |
| --- | --- | --- |
| `start_date` | `2026-11-01` | 이 날짜 이후에 끝나는 축제 (기본: 오늘) |
| `end_date` | `2026-11-30` | 이 날짜 이전에 시작하는 축제 |
| `area_code` | `1,31` | 쉼표로 여러 개 |
| `tags` | `music,food` | 하나라도 겹치면 포함 |
| `status` | `ongoing` | `upcoming` / `ongoing` (기본: 둘 다, 종료 제외) |
| `keyword` | `빛` | 축제명 검색 |
| `sort` | `start_date` | `start_date`(기본) / `end_date` / `title` |
| `page`, `size` | | 공통 규칙 |

응답: 목록 형식, `items`는 FestivalSummary 배열

**GET `/api/festivals/recommended`**

- 파라미터: `size` (기본 10)
- 응답: FestivalSummary에 `score`(0~100), `reason`(추천 이유 한 문장)을 더한 배열

```json
[ { /* FestivalSummary */, "score": 87, "reason": "좋아하시는 야경 축제이고 선호 지역인 서울에서 열려요." } ]
```

- `reason`은 AI가 작성하므로 느릴 수 있음. 홈 화면은 로딩 표시 필요
- 첫 설정을 안 한 사용자: 400 `ONBOARDING_REQUIRED`

**GET `/api/festivals/{content_id}`** → FestivalDetail. 없으면 404 `FESTIVAL_NOT_FOUND`

**GET `/api/festivals/{content_id}/similar`** → FestivalSummary 배열 (최대 6개)

---

## 5. 주변 장소 (BE1 / FE1·FE2)

**GET `/api/places/nearby`**

| 파라미터 | 예시 | 설명 |
| --- | --- | --- |
| `content_id` | `2786391` | 기준 축제 (필수) |
| `category` | `restaurant` | `attraction` / `restaurant` / `cafe` (필수) |
| `radius` | `3000` | 미터, 기본 3000, 최대 20000 |
| `page`, `size` | | 공통 규칙 |

응답: 목록 형식, `items`는 Place 배열 (가까운 순)

---

## 6. 일정 계산 (BE1 / FE2)

**POST `/api/itinerary/calculate`** 🔓 — 저장하지 않고 시간표만 계산

```json
// 요청
{
  "festival_content_id": "2786391",
  "visit_date": "2026-11-02",
  "start_time": "10:00",
  "end_time": "21:00",
  "place_ids": ["126508", "2871024"],
  "auto_fill": true
}
```

- `place_ids`: 사용자가 고른 주변 장소 (없으면 `[]`)
- `auto_fill`: `true`면 부족한 식사·관광지를 자동으로 채움
- 응답: Itinerary
- 일정을 만들 수 없으면 400 + `code`: `VISIT_DATE_OUT_OF_RANGE`(축제 기간 아님), `TIME_TOO_SHORT`(시간 부족)
- 이동 시간 계산 때문에 수 초 걸릴 수 있음 → 로딩 표시

---

## 7. AI 채팅 (BE1 / FE2)

**POST `/api/agent/chat`** 🔓 — 요청·응답 형식은 [agent-response-format.md](agent-response-format.md)

---

## 8. 찜 (BE2 / FE1)

| 메서드 | 주소 | | 설명 |
| --- | --- | --- | --- |
| GET | `/api/likes` | 🔒 | 내 찜 목록 (목록 형식, items = FestivalSummary) |
| POST | `/api/likes` | 🔒 | 찜하기 `{ "content_id": "2786391" }` → 201 |
| DELETE | `/api/likes/{content_id}` | 🔒 | 찜 취소 → 204 |

- 이미 찜한 축제면 409 `ALREADY_LIKED`. 프론트는 409도 "찜됨" 상태로 처리하면 됨

---

## 9. 일정 저장 (BE2 / FE2)

| 메서드 | 주소 | | 설명 |
| --- | --- | --- | --- |
| GET | `/api/schedules` | 🔒 | 내 일정 목록 |
| POST | `/api/schedules` | 🔒 | 일정 저장 |
| GET | `/api/schedules/{id}` | 🔒 | 일정 상세 |
| PUT | `/api/schedules/{id}` | 🔒 | 일정 수정 (다시 계산한 결과로 전체 교체) |
| DELETE | `/api/schedules/{id}` | 🔒 | 삭제 → 204 |

**POST `/api/schedules`**

```json
// 요청: Itinerary (warnings 제외) + title
{ "title": "빛초롱 데이트", "festival_content_id": "2786391", "visit_date": "2026-11-02", "start_time": "10:00", "end_time": "21:00", "total_travel_min": 55, "items": [ /* ... */ ] }
// 응답 201
{ "id": 7, "title": "빛초롱 데이트", /* Itinerary */, "festival": { /* FestivalSummary */ }, "created_at": "..." }
```

**GET `/api/schedules`** 목록 항목

```json
{ "id": 7, "title": "빛초롱 데이트", "visit_date": "2026-11-02", "festival": { /* FestivalSummary */ }, "item_count": 5 }
```

- 남의 일정 접근 시 404 (존재 여부를 숨김)

---

## 10. 커뮤니티 (BE2 / FE3)

| 메서드 | 주소 | | 설명 |
| --- | --- | --- | --- |
| GET | `/api/posts` | | 글 목록 `?page&size&festival_content_id` |
| POST | `/api/posts` | 🔒 | 글쓰기 |
| GET | `/api/posts/{id}` | | 글 상세 (조회수 +1) |
| PUT | `/api/posts/{id}` | 🔒 | 수정 (작성자만) |
| DELETE | `/api/posts/{id}` | 🔒 | 삭제 (작성자만) → 204 |
| GET | `/api/posts/{id}/comments` | | 댓글 목록 (오래된 순) |
| POST | `/api/posts/{id}/comments` | 🔒 | 댓글 쓰기 `{ "content": "..." }` |
| DELETE | `/api/comments/{id}` | 🔒 | 댓글 삭제 (작성자만) → 204 |

```json
// POST /api/posts 요청
{ "title": "빛초롱 다녀왔어요", "content": "...", "festival_content_id": "2786391" }

// 글 (목록 항목 / 상세 공통)
{
  "id": 12,
  "title": "빛초롱 다녀왔어요",
  "content": "...",
  "author": { "id": 3, "nickname": "축제러버" },
  "festival": { "content_id": "2786391", "title": "서울빛초롱축제" },
  "view_count": 31,
  "comment_count": 4,
  "is_mine": true,
  "created_at": "2026-10-28T09:00:00+09:00",
  "updated_at": "2026-10-28T09:00:00+09:00"
}
```

- 목록에서는 `content`를 앞 100자만 줌
- `festival`은 관련 축제가 없으면 `null`

---

## 11. 알림 (BE2 / FE3)

| 메서드 | 주소 | | 설명 |
| --- | --- | --- | --- |
| GET | `/api/notifications` | 🔒 | 알림 목록 (최신 순, 목록 형식) |
| GET | `/api/notifications/unread-count` | 🔒 | `{ "count": 3 }` — 헤더 배지용 |
| PATCH | `/api/notifications/{id}/read` | 🔒 | 읽음 처리 → 204 |
| PATCH | `/api/notifications/read-all` | 🔒 | 모두 읽음 → 204 |

```json
{
  "id": 41,
  "type": "FESTIVAL_D1",
  "message": "찜한 '서울빛초롱축제'가 내일 시작해요!",
  "festival_content_id": "2786391",
  "is_read": false,
  "created_at": "2026-10-31T09:00:00+09:00"
}
```

- `type` 종류는 [db-schema.md](db-schema.md)의 notifications 참고
