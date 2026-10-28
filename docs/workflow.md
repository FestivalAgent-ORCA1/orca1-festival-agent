# AI 작업 흐름 설계안

> 담당: BE1 · 상태: **초안**
>
> 사용자 요청이 들어왔을 때 AI와 Tool이 어떤 순서로 움직이는지 정리합니다.
> Tool 상세는 [tool-spec.md](tool-spec.md), 응답 모양은 [agent-response-format.md](agent-response-format.md).

## 전체 구조

```text
[프론트] POST /api/agent/chat
   │
   ▼
api/agent.py ──▶ agent/intent.py      ① 의도 분류 (recommend / festival_info / itinerary / smalltalk / unknown)
   │
   ├─ recommend, festival_info ──▶ agent/loop.py      ② AI가 Tool을 골라 실행 (최대 5회)
   │
   ├─ itinerary ──▶ services/itinerary_service.py    ③ 정해진 순서로 실행 (AI는 값 추출·설명만)
   │
   └─ smalltalk, unknown ──▶ Tool 없이 AI 답변 1번
   │
   ▼
blocks 배열로 정리해서 응답
```

### 왜 일정은 AI 반복 처리에 맡기지 않나요?

일정 만들기는 "축제 정보 → 주변 장소 → 순서 배치 → 이동 시간 → 검사"로 **순서가 항상 같습니다**.
AI가 매번 Tool을 고르게 하면 단계를 건너뛰거나 호출 수가 늘어날 수 있으므로,
코드로 순서를 고정하고 AI는 **사용자 말에서 값을 뽑는 일**과 **결과를 설명하는 일**만 합니다.
같은 서비스 함수를 `POST /api/itinerary/calculate`도 그대로 사용합니다.

---

## ① 의도 분류 (`agent/intent.py`)

- Groq에 짧은 분류 지시문 + 사용자 메시지(+ 최근 대화 2~3개)를 보내 `intent` 하나를 JSON으로 받음
- 빠른 처리를 위해 간단한 키워드 규칙을 먼저 적용 ("일정", "코스", "시간표" → itinerary)하고, 애매할 때만 AI 호출
- `context.festival_content_id`나 `context.itinerary`가 있고 일정 관련 표현이면 itinerary

## ② AI 반복 처리 (`agent/loop.py`)

```text
messages = [시스템 지시문(오늘 날짜·요일, 사용자 관심사), 이전 대화, 사용자 메시지]
for 회차 in 1..5:
    응답 = Groq(messages, tools=tool_schemas)
    if 응답에 tool 호출 없음:
        → 최종 답변. 반복 종료
    for 각 tool 호출:
        결과 = 해당 Tool 함수 실행 (실패해도 {"ok": False, ...} 반환)
        messages에 결과 추가
5회를 넘기면 → "질문을 조금 더 구체적으로 알려주세요" 안내
```

- 이 경로에서 AI가 쓸 수 있는 Tool: `search_festivals`, `get_festival_detail`, `score_festivals`
- AI의 최종 답변은 **글만** 작성. 축제 카드 블록은 AI가 만든 JSON이 아니라, 이번 요청에서 Tool이 돌려준 축제 데이터로 **서버가 직접** 만듦 (AI가 축제 정보를 지어내지 않도록)
- AI가 답변에 "추천한 축제 ID 목록"을 함께 돌려주게 하고(JSON 응답 형식), 그 ID만 카드로 만듦

### 추천 흐름 예시 — "이번 주말 서울 축제 추천해줘"

```text
1. search_festivals(start_date=토요일, end_date=일요일, area_codes=["1"])
2. score_festivals(festivals, profile, liked_ids)      ← 로그인 사용자만. 비로그인은 생략
3. AI가 상위 3~5개를 골라 추천 이유 작성 → text + festival_cards + quick_replies
```

## ③ 일정 생성 (`services/itinerary_service.py`)

```text
0. AI로 값 추출: 축제(content_id 또는 축제명), 방문일, 시작·종료 시각, 원하는 장소 종류
   └ 빠진 값이 있으면 → 되묻기 (text + quick_replies) 하고 종료
      기본값: 시작 10:00, 종료 21:00 (사용자가 말하지 않으면 그대로 사용하고 답변에 알려줌)
1. get_festival_detail(content_id)
2. search_nearby_places(축제 좌표, attraction / restaurant / cafe)
3. build_timeline(...)                 ← 직선거리로 순서·시간 먼저 배치
4. calc_travel_time(이웃한 장소 쌍)     ← 정해진 순서대로 N-1번만
5. build_timeline(..., travel_legs)    ← 실제 이동 시간으로 다시 배치
6. validate_schedule(...)
   └ errors 있으면 장소를 하나 빼고 3번부터 다시 (최대 2회)
7. AI가 시간표를 2~3문장으로 설명 → text + timeline + quick_replies
```

- **일정 수정** ("카페 추가해줘", "18시까지"): `context.itinerary`를 출발점으로, 바뀐 조건만 반영해서 3번부터 다시 실행

---

## 자동 실행 작업 (`batch/`, APScheduler)

| 작업 | 시각 (한국 시간) | 담당 | 하는 일 |
| --- | --- | --- | --- |
| `sync_festivals` | 매주 월요일 04:00 | BE1 | 오늘~90일 뒤 축제를 `searchFestival2`로 받아 `festivals`에 저장·갱신. `modifiedtime`이 바뀐 축제만 상세·소개 다시 받기 |
| `extract_tags` | `sync_festivals` 끝난 직후 | BE1 | 태그가 없거나 소개글이 바뀐 축제만 AI로 태그 1~3개 붙이기 |
| `send_notifications` | 매일 09:00 | BE2 | 찜 알림 만들기 (아래) |

### 찜 알림 (`send_notifications`)

```text
각 사용자의 찜한 축제마다:
  시작 7일 전  → FESTIVAL_D7      "찜한 '{축제명}'가 일주일 뒤 시작해요"
  시작 1일 전  → FESTIVAL_D1      "찜한 '{축제명}'가 내일 시작해요!"
  시작 당일    → FESTIVAL_START   "'{축제명}'가 오늘 시작했어요"
  찜한 축제가 끝난 다음 날 → similar_festivals()로 1개 골라 SIMILAR_FESTIVAL
```

- 같은 알림이 두 번 만들어지지 않도록 DB UNIQUE 제약 사용 ([db-schema.md](db-schema.md))
- Render 무료 플랜은 요청이 없으면 서버가 잠들어 예약 작업이 안 돌 수 있음 → 6주차 배포 때 외부 cron으로 깨우는 방법 확인 (BE2)

---

## AI 지시문 원칙 (`agent/prompts.py`)

- 오늘 날짜와 요일을 항상 넣기 (예: `오늘은 2026-10-28(수)입니다.`) — "이번 주말" 계산용
- Tool 결과에 없는 축제명·날짜·요금을 **지어내지 말 것**. 모르면 모른다고 답하기
- 한국어 존댓말, 마크다운 금지, 한 답변 3~5문장 이내
- 서비스 범위(국내 축제·여행 일정) 밖 질문은 정중히 안내
- Groq 모델은 Tool 호출을 지원하는 모델로 선택하고 이름은 `.env`의 `GROQ_MODEL`로 관리 (바꾸기 쉽게)
