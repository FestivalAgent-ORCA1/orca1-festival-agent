"""AI 채팅의 일정 경로 (docs/workflow.md ③)

AI는 사용자 말에서 값(축제명·방문일·시각·추가/뺄 장소)을 뽑는 일만 한다 (Groq 1번).
나머지는 itinerary_service가 정해진 순서로 계산하고, 설명 문장은 템플릿으로 만든다
(Groq 무료 플랜 분당 토큰 제한 때문에 설명용 AI 호출은 생략).
"""

import logging
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.agent import prompts
from app.agent.client import chat_json
from app.core.errors import AppError
from app.models.festival import Festival
from app.services import festival_service, itinerary_service
from app.services.festival_service import today_kst
from app.tools.build_timeline import to_min

logger = logging.getLogger(__name__)

DEFAULT_START, DEFAULT_END = "10:00", "21:00"
CATEGORY_NAMES = {"attraction": "관광지", "restaurant": "식당", "cafe": "카페"}
EXTRACT_PROMPT = (
    "사용자와의 대화에서 축제 일정(시간표)을 만들 정보를 뽑아.\n{date_line}\n{context}"
    "모르는 값은 null. 시각은 24시간 HH:MM ('저녁 6시까지' → end_time 18:00).\n"
    "add_categories: 추가해 달라는 장소 종류 (attraction=관광지, restaurant=식당·맛집, cafe=카페).\n"
    "remove_names: 빼 달라는 장소 이름.\n"
    'JSON으로만 답해: {{"festival_name": null, "visit_date": null, "start_time": null, "end_time": null, '
    '"add_categories": [], "remove_names": []}}'
)


def _context_line(festival_title: str | None, itinerary: dict | None) -> str:
    lines = []
    if festival_title:
        lines.append(f"사용자는 '{festival_title}' 축제 화면에서 묻고 있어.")
    if itinerary:
        names = ", ".join(i.get("name", "") for i in itinerary.get("items", []))
        lines.append(
            f"화면의 현재 일정: {itinerary.get('visit_date')} {itinerary.get('start_time')}~{itinerary.get('end_time')}, 장소: {names}. "
            "사용자가 바꾸라고 한 값만 채워."
        )
    return "\n".join(lines) + ("\n" if lines else "")


def _valid_time(value) -> str | None:
    try:
        return value if isinstance(value, str) and 0 <= to_min(value) < 24 * 60 and len(value) == 5 else None
    except ValueError:
        return None


def _valid_date(value) -> date | None:
    try:
        return date.fromisoformat(value) if isinstance(value, str) else None
    except ValueError:
        return None


def _text(value: str) -> list[dict]:
    return [{"type": "text", "text": value}]


def _quick(options: list[tuple[str, str]]) -> dict:
    return {"type": "quick_replies", "options": [{"label": l, "message": m} for l, m in options][:4]}


def _date_options(festival: dict, title: str) -> list[tuple[str, str]]:
    """축제 기간 안에서 고를 만한 날짜 (오늘 이후, 주말 우선)"""
    today = today_kst()
    start = max(date.fromisoformat(festival["start_date"]), today)
    end = date.fromisoformat(festival["end_date"])
    days = [start + timedelta(days=n) for n in range((end - start).days + 1)][:60]
    picked = [d for d in days if d.weekday() >= 5][:2] or days[:2]
    return [(f"{d.month}월 {d.day}일({prompts.WEEKDAYS[d.weekday()]})", f"{title} {d.isoformat()}에 갈 거야") for d in picked]


def summary_text(itinerary: dict, title: str, used_default_time: bool) -> str:
    d = date.fromisoformat(str(itinerary["visit_date"]))
    places = [i for i in itinerary["items"] if i["category"] != "festival"]
    fest = next((i for i in itinerary["items"] if i["category"] == "festival"), None)
    parts = [f"{d.month}월 {d.day}일 {title} 일정을 만들었어요."]
    if fest:
        parts.append(f"축제는 {fest['start_time']}~{fest['end_time']}에 둘러보는 코스예요.")
    meals = [i["name"] for i in places if i["category"] == "restaurant"]
    if meals:
        parts.append("식사는 " + ", ".join(meals) + "에서 해요.")
    if itinerary["total_travel_min"]:
        parts.append(f"이동은 모두 합쳐 약 {itinerary['total_travel_min']}분이에요 (자동차 기준).")
    if used_default_time:
        parts.append(f"시간을 말씀하지 않으셔서 {itinerary['start_time']}~{itinerary['end_time']}로 잡았어요.")
    return " ".join(parts)


def _find_festival(db: Session, name: str | None) -> dict | None:
    if not name:
        return None
    items = festival_service.list_festivals(db, keyword=name, size=5)["items"]
    if not items:  # 공백·조사 때문에 못 찾으면 앞 단어로 한 번 더
        first = name.split()[0] if name.split() else ""
        if first and first != name:
            items = festival_service.list_festivals(db, keyword=first, size=5)["items"]
    return items[0] if items else None


def run_itinerary_chat(db: Session, message: str, history: list[dict], context: dict) -> dict:
    """{"intent": "itinerary", "blocks": [...]}. Groq 실패는 AiError로 올려 보냄 (API에서 502)"""
    current = context.get("itinerary") or None
    festival_id = (current or {}).get("festival_content_id") or context.get("festival_content_id")
    festival_row = db.get(Festival, str(festival_id)) if festival_id else None

    extract = chat_json(
        [
            {"role": "system", "content": EXTRACT_PROMPT.format(
                date_line=prompts.date_line(today_kst()),
                context=_context_line(festival_row.title if festival_row else None, current))},
            *({"role": h["role"], "content": h["text"]} for h in history[-4:]),
            {"role": "user", "content": message},
        ],
        temperature=0,
        max_tokens=400,
    )

    festival = festival_service.to_summary(festival_row) if festival_row else None
    if festival is None:
        festival = _find_festival(db, extract.get("festival_name"))
    if festival is None:
        return {"intent": "itinerary", "blocks": _text("어떤 축제로 일정을 짤까요? 축제 이름을 알려주세요.") + [
            _quick([("이번 주말 축제 추천", "이번 주말에 갈 만한 축제 추천해줘")])]}
    title = festival["title"]
    festival_dates = {"start_date": str(festival["start_date"]), "end_date": str(festival["end_date"])}

    visit = _valid_date(extract.get("visit_date")) or _valid_date((current or {}).get("visit_date"))
    if visit is None and festival_dates["start_date"] == festival_dates["end_date"]:
        visit = date.fromisoformat(festival_dates["start_date"])  # 하루짜리 축제
    if visit is None:
        return {"intent": "itinerary", "blocks": _text(f"{title}에 언제 방문하실 예정인가요?") + [
            _quick(_date_options(festival_dates, title))]}

    start = _valid_time(extract.get("start_time")) or (current or {}).get("start_time")
    end = _valid_time(extract.get("end_time")) or (current or {}).get("end_time")
    used_default = not start or not end
    start, end = start or DEFAULT_START, end or DEFAULT_END

    removed = {str(n) for n in extract.get("remove_names") or []}
    place_ids = [
        i["content_id"] for i in (current or {}).get("items", [])
        if i.get("category") != "festival" and i.get("content_id")
        and not any(r and (r in i.get("name", "") or i.get("name", "") in r) for r in removed)
    ]
    try:
        itinerary = itinerary_service.calculate(
            db, festival["content_id"], visit, start, end, place_ids,
            auto_fill=current is None,  # 처음 만들 때만 자동 채우기, 수정할 때는 있는 장소 유지
            extra_categories=[c for c in extract.get("add_categories") or [] if c in CATEGORY_NAMES],
        )
    except AppError as exc:
        options = _date_options(festival_dates, title) if exc.code == "VISIT_DATE_OUT_OF_RANGE" else [
            ("10시~21시로 다시", f"{title} {visit.isoformat()} 10시부터 21시까지 일정 짜줘")]
        return {"intent": "itinerary", "blocks": _text(exc.message) + [_quick(options)]}

    blocks = _text(summary_text(itinerary, title, used_default))
    blocks.append({"type": "timeline", "itinerary": itinerary, "savable": True})
    blocks.append(_quick([("카페 추가해줘", "중간에 카페도 넣어줘"), ("더 일찍 끝내줘", "18시까지 끝나게 바꿔줘"),
                          ("관광지 더 넣어줘", "관광지 한 곳 더 넣어줘")]))
    return {"intent": "itinerary", "blocks": blocks}
