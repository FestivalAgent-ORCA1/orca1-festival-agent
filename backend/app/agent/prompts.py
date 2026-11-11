"""AI 지시문 (docs/workflow.md 'AI 지시문 원칙')

- 오늘 날짜·요일을 항상 넣는다 (모델은 오늘 날짜를 모름 → "이번 주말" 계산용)
- Tool 결과에 없는 정보를 지어내지 않게 한다
- 최종 답변은 final_answer Tool로 받음 (서버가 축제 카드를 Tool 결과로 직접 만들기 위해 festival_ids만 받음)
- 무료 플랜 분당 토큰 제한(8,000)이 있어 지시문은 짧게 유지
"""

from datetime import date, timedelta

from app.core.constants import AGE_GROUPS, REGION_NAMES, TAGS

WEEKDAYS = "월화수목금토일"
TAG_NAMES = {t["code"]: t["name"] for t in TAGS}
AGE_NAMES = {a["code"]: a["name"] for a in AGE_GROUPS}


def date_line(today: date) -> str:
    saturday = today + timedelta(days=(5 - today.weekday()) % 7)
    return (
        f"오늘은 {today.isoformat()}({WEEKDAYS[today.weekday()]})입니다. "
        f"'이번 주말'은 {saturday.isoformat()}(토)~{(saturday + timedelta(days=1)).isoformat()}(일)입니다."
    )


def profile_line(profile: dict | None) -> str:
    if not profile:
        return "사용자 취향 정보: 없음 (비로그인 또는 첫 설정 전)."
    parts = []
    if profile.get("age_group"):
        parts.append(f"연령대 {AGE_NAMES.get(profile['age_group'], profile['age_group'])}")
    regions = [REGION_NAMES.get(c, c) for c in profile.get("regions") or []]
    parts.append("선호 지역 " + (", ".join(regions) if regions else "전국"))
    tags = [TAG_NAMES.get(c, c) for c in profile.get("tags") or []]
    if tags:
        parts.append("관심사 " + ", ".join(tags))
    return "사용자 취향 정보: " + " / ".join(parts) + "."


def chat_system_prompt(today: date, profile: dict | None, context_festival_id: str | None = None) -> str:
    lines = [
        "너는 국내 축제를 추천하고 축제 정보를 안내하는 '축제 AI 에이전트'야.",
        date_line(today),
        profile_line(profile),
        "",
        "규칙:",
        "- 축제를 찾거나 정보를 답할 때는 반드시 Tool을 먼저 호출해. 축제명·날짜·장소·요금·시간은 Tool 결과에 있는 것만 말해.",
        "- Tool 결과에 없으면 모른다고 솔직히 말해. 지어내지 마.",
        "- 사용자가 지역·관심사를 말하지 않았고 취향 정보가 있으면 그것을 참고해서 찾아.",
        "- 결과가 없으면 기간이나 지역을 넓혀서 한 번 더 찾아봐.",
        "- 한국어 존댓말, 마크다운 금지, text는 3~5문장 이내.",
        "- 국내 축제·여행과 관계없는 질문은 정중히 범위 밖이라고 안내해.",
    ]
    if context_festival_id:
        lines.append(f"- 사용자는 지금 content_id={context_festival_id} 축제 상세 화면에서 질문하고 있어.")
    lines += [
        "",
        "답변은 항상 final_answer Tool을 호출해서 보내.",
        "intent: 추천·검색=recommend, 특정 축제 질문=festival_info, 인사·사용법=smalltalk, 범위 밖=unknown.",
        "quick_replies 예: 'OO축제로 일정 짜줘', '다른 지역도 보여줘'.",
    ]
    return "\n".join(lines)
