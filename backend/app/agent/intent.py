"""의도 분류 (docs/workflow.md ①)

빠른 처리를 위해 키워드 규칙을 먼저 적용한다. 규칙으로 '일정'이 아니면 AI 반복 처리(loop.py)로 보내고,
recommend / festival_info / smalltalk / unknown 구분은 loop의 최종 답변 JSON의 intent로 받는다.
(분류만을 위한 AI 호출을 따로 하지 않아 Groq 무료 사용량과 응답 시간을 아낌)
"""

import re

INTENTS = ("recommend", "festival_info", "itinerary", "smalltalk", "unknown")

ITINERARY_WORDS = re.compile(r"일정|코스|시간표|동선|루트|하루\s*계획|짜\s*줘|짜줄래|짜 ?주세요")
# 화면에 시간표가 있을 때 수정 요청으로 볼 표현
EDIT_WORDS = re.compile(r"추가|넣어|빼|바꿔|변경|까지|부터|일찍|늦게|대신|수정")


def classify_by_rules(message: str, context: dict | None = None) -> str | None:
    """'itinerary'면 일정 경로, None이면 AI 반복 처리로"""
    context = context or {}
    if ITINERARY_WORDS.search(message):
        return "itinerary"
    if context.get("itinerary") and EDIT_WORDS.search(message):
        return "itinerary"
    return None
