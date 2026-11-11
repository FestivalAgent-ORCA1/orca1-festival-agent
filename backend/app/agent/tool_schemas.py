"""AI에게 주는 Tool 설명서 (docs/tool-spec.md 기준, OpenAI 호환 function 형식)

추천·축제 정보 경로(agent/loop.py)에서 AI가 고를 수 있는 Tool만 둔다.
score_festivals는 3주차(A6)에 추가. 일정 Tool은 itinerary_service가 순서대로 호출하므로 여기 없음.
"""

from app.core.constants import REGIONS, TAGS

SEARCH_FESTIVALS = {
    "type": "function",
    "function": {
        "name": "search_festivals",
        "description": (
            "기간·지역·관심사 태그·키워드로 국내 축제를 찾는다. 축제명을 아는 경우 keyword에 축제명 일부를 넣는다. "
            "결과에 없는 축제는 절대 언급하지 않는다."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "description": "YYYY-MM-DD. 이 날짜 이후에 끝나는 축제"},
                "end_date": {"type": "string", "description": "YYYY-MM-DD. 이 날짜 이전에 시작하는 축제 (생략 시 시작일+30일)"},
                "area_codes": {
                    "type": "array",
                    "items": {"type": "string", "enum": [r["code"] for r in REGIONS]},
                    "description": "지역 코드: " + ", ".join(f"{r['code']}={r['name']}" for r in REGIONS),
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string", "enum": [t["code"] for t in TAGS]},
                    "description": "관심사 태그(하나라도 겹치면 포함): " + ", ".join(f"{t['code']}={t['name']}" for t in TAGS),
                },
                "keyword": {"type": "string", "description": "축제명 또는 주소 일부"},
                "limit": {"type": "integer", "description": "최대 개수 (기본 20, 최대 50)"},
            },
            "required": ["start_date"],
        },
    },
}

GET_FESTIVAL_DETAIL = {
    "type": "function",
    "function": {
        "name": "get_festival_detail",
        "description": "축제 1개의 장소, 운영 시간, 요금, 소개, 연락처를 가져온다. content_id는 search_festivals 결과에서 얻는다.",
        "parameters": {
            "type": "object",
            "properties": {"content_id": {"type": "string", "description": "축제 content_id"}},
            "required": ["content_id"],
        },
    },
}

# 최종 답변도 Tool로 받는다 (gpt-oss는 "JSON으로 답해"라고 하면 없는 'json' Tool을 부르려 해서 오류가 남)
FINAL_ANSWER = {
    "type": "function",
    "function": {
        "name": "final_answer",
        "description": "사용자에게 보낼 최종 답변. 정보 수집이 끝나면 반드시 이 Tool을 한 번 호출해서 답한다.",
        "parameters": {
            "type": "object",
            "properties": {
                "intent": {"type": "string", "enum": ["recommend", "festival_info", "smalltalk", "unknown"]},
                "text": {"type": "string", "description": "답변 글. 존댓말, 마크다운 없이 3~5문장"},
                "festival_ids": {
                    "type": "array", "items": {"type": "string"},
                    "description": "카드로 보여줄 축제 content_id (Tool 결과에 있던 것만, 최대 5개)",
                },
                "reasons": {
                    "type": "object", "additionalProperties": {"type": "string"},
                    "description": "{content_id: 추천 이유 한 문장} (추천일 때만)",
                },
                "quick_replies": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {"label": {"type": "string"}, "message": {"type": "string"}},
                        "required": ["label", "message"],
                    },
                    "description": "다음에 할 만한 행동 2~3개",
                },
            },
            "required": ["intent", "text"],
        },
    },
}

CHAT_TOOLS = [SEARCH_FESTIVALS, GET_FESTIVAL_DETAIL, FINAL_ANSWER]
