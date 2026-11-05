# AI 채팅 응답 형식

> 담당: BE1 · FE2 · 상태: **초안**
>
> `POST /api/agent/chat`의 요청·응답 형식입니다. 블록 종류를 추가할 때는 두 사람이 함께 이 문서를 고칩니다.

## 핵심 아이디어

AI 답변 1개 = **블록(block) 여러 개의 배열**.
프론트는 블록을 위에서부터 순서대로 그리기만 하면 됩니다. `type`에 따라 그리는 컴포넌트가 다릅니다.

| `type` | 화면 | 컴포넌트 |
| --- | --- | --- |
| `text` | 말풍선 글 | `MessageBubble` |
| `festival_cards` | 축제 카드 가로 스크롤 | `FestivalCard` (FE1 컴포넌트 재사용) |
| `timeline` | 시간표 + 지도 | `Timeline`, `KakaoMap` |
| `quick_replies` | 선택지 버튼 | `QuickReply` |

> 프론트가 모르는 `type`이 오면 **무시**합니다 (오류 내지 않기). 그래야 백엔드가 블록을 먼저 추가해도 화면이 깨지지 않습니다.

---

## 요청

```json
{
  "message": "이번 주말에 서울 근처에서 갈 만한 축제 있어?",
  "history": [
    { "role": "user", "text": "안녕" },
    { "role": "assistant", "text": "안녕하세요! 어떤 축제를 찾으세요?" }
  ],
  "context": {
    "festival_content_id": null
  }
}
```

| 필드 | 필수 | 설명 |
| --- | --- | --- |
| `message` | O | 사용자가 보낸 글 (1~500자) |
| `history` | X | 이전 대화. **최근 10개까지**, 글(`text`)만 보냄. 카드·시간표 블록 내용은 보내지 않음 |
| `context.festival_content_id` | X | 축제 상세 페이지에서 "이 축제로 일정 짜기"로 들어온 경우 해당 축제 ID |
| `context.itinerary` | X | 화면에 있는 마지막 시간표 (일정 수정 요청용, 아래 "예시 모음" 마지막 참고) |

- 대화 기록은 서버에 저장하지 않습니다 (프론트가 화면 state로 들고 있다가 보냄). 새로고침하면 대화가 사라지는 건 1차 범위에서 허용
- `history`의 assistant 글은 해당 응답의 `text` 블록들을 이어 붙인 것
- 로그인했으면 `Authorization` 헤더를 꼭 보내기 → 추천에 사용자 관심사·찜 목록이 반영됨

## 응답

```json
{
  "intent": "recommend",
  "blocks": [
    { "type": "text", "text": "이번 주말 서울 근처에서 열리는 축제를 골라봤어요!" },
    {
      "type": "festival_cards",
      "items": [
        {
          "festival": { /* FestivalSummary (api-spec.md) */ },
          "reason": "좋아하시는 야경 축제예요."
        }
      ]
    },
    {
      "type": "quick_replies",
      "options": [
        { "label": "첫 번째 축제로 일정 짜줘", "message": "서울빛초롱축제로 일정 짜줘" },
        { "label": "다른 지역도 보여줘", "message": "다른 지역 축제도 보여줘" }
      ]
    }
  ]
}
```

### `intent` 값

| 값 | 뜻 |
| --- | --- |
| `recommend` | 축제 추천·검색 |
| `festival_info` | 특정 축제 정보 질문 (기간, 요금, 위치 등) |
| `itinerary` | 일정(시간표) 만들기·수정 |
| `smalltalk` | 인사, 서비스 사용법 등 |
| `unknown` | 서비스 범위 밖 질문 (AI가 정중히 안내) |

프론트는 `intent`를 화면 분기에 쓰지 않아도 됩니다 (분석·디버깅용). 화면은 `blocks`만 보고 그립니다.

---

## 블록 상세

### `text`

```json
{ "type": "text", "text": "글 내용" }
```

- 줄바꿈은 `\n`. 마크다운은 쓰지 않음 (AI 지시문에서 금지)

### `festival_cards`

```json
{
  "type": "festival_cards",
  "items": [ { "festival": { /* FestivalSummary */ }, "reason": "추천 이유 한 문장" } ]
}
```

- 최대 5개. 카드를 누르면 `/festivals/{content_id}`로 이동
- `reason`은 없을 수 있음 (`null`)

### `timeline`

```json
{
  "type": "timeline",
  "itinerary": { /* Itinerary (api-spec.md) */ },
  "savable": true
}
```

- `savable: true`면 "일정 저장" 버튼 표시 → 누르면 `itinerary`를 그대로 `POST /api/schedules`로 보냄 (로그인 필요)
- `itinerary.warnings`가 있으면 시간표 위에 안내 문구로 표시

### `quick_replies`

```json
{
  "type": "quick_replies",
  "options": [ { "label": "버튼에 보일 글", "message": "누르면 보낼 글" } ]
}
```

- 버튼을 누르면 `message`를 사용자가 직접 입력한 것처럼 전송 (말풍선에도 `message` 표시)
- 항상 응답의 **마지막 블록**. 최대 4개
- 새 메시지를 보내면 이전 선택지 버튼은 숨김

---

## 오류·지연 처리

| 상황 | 백엔드 | 프론트 |
| --- | --- | --- |
| Tool(TourAPI·카카오) 일부 실패 | **200**으로 응답하되, 가능한 내용 + 안내 `text` 블록 | 평소처럼 그리기 |
| Groq 호출 실패·한도 초과 | 502 `EXTERNAL_API_ERROR` | "잠시 후 다시 시도해주세요" 말풍선 + 다시 보내기 버튼 |
| 반복 처리 5회 초과 | 200 + "질문을 조금 더 구체적으로..." `text` 블록 | 평소처럼 그리기 |
| 응답 지연 | 목표 10초 이내 | 요청 타임아웃 **30초**, 기다리는 동안 "답변 작성 중..." 표시 |

## 예시 모음

### 축제 정보 질문 — "빛초롱축제 입장료 얼마야?"

```json
{
  "intent": "festival_info",
  "blocks": [
    { "type": "text", "text": "서울빛초롱축제는 무료로 입장할 수 있어요. 운영 시간은 17:00~22:00예요." },
    { "type": "festival_cards", "items": [ { "festival": { /* ... */ }, "reason": null } ] }
  ]
}
```

### 일정 요청인데 정보가 부족할 때 — "빛초롱축제 일정 짜줘"

```json
{
  "intent": "itinerary",
  "blocks": [
    { "type": "text", "text": "언제 방문하실 예정인가요?" },
    {
      "type": "quick_replies",
      "options": [
        { "label": "이번 토요일", "message": "이번 토요일에 갈 거야" },
        { "label": "이번 일요일", "message": "이번 일요일에 갈 거야" }
      ]
    }
  ]
}
```

### 일정 생성 완료

```json
{
  "intent": "itinerary",
  "blocks": [
    { "type": "text", "text": "11월 2일 일정을 만들었어요. 점심은 토속촌, 저녁엔 빛초롱축제를 보는 코스예요." },
    { "type": "timeline", "itinerary": { /* ... */ }, "savable": true },
    {
      "type": "quick_replies",
      "options": [
        { "label": "카페 추가해줘", "message": "중간에 카페도 넣어줘" },
        { "label": "더 일찍 끝내줘", "message": "18시까지 끝나게 바꿔줘" }
      ]
    }
  ]
}
```

> 일정 수정 요청("카페 추가해줘")은 `history`의 글만으로는 이전 시간표를 알 수 없으므로,
> 프론트는 마지막 `timeline` 블록의 `itinerary`를 `context.itinerary`에 담아 보냅니다. (2주차에 BE1·FE2가 확정)
