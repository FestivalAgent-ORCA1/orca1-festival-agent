"""AI 반복 처리 (docs/workflow.md ②) — AI가 Tool을 고르고, 서버가 실행하고, 결과를 다시 AI에게

- 최대 MAX_ROUNDS회. 넘으면 "조금 더 구체적으로" 안내
- 축제 카드는 AI가 만든 JSON이 아니라 이번 요청에서 Tool이 돌려준 축제 데이터로 서버가 직접 만든다
  (AI는 festival_ids만 고름 → 축제 정보를 지어낼 수 없음)
- AI에게 보내는 Tool 결과는 토큰을 아끼려고 필요한 필드만 (compact_*)
"""

import json
import logging
import re
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.agent import prompts
from app.agent.client import chat
from app.agent.intent import INTENTS
from app.agent.tool_schemas import CHAT_TOOLS
from app.services.festival_service import today_kst
from app.services.recommend_service import liked_tags_of
from app.tools.get_festival_detail import get_festival_detail
from app.tools.score_festivals import score_one
from app.tools.search_festivals import search_festivals

logger = logging.getLogger(__name__)

MAX_ROUNDS = 5
AI_SEARCH_LIMIT = 10  # AI에게 보내는 축제 수 (무료 플랜 분당 토큰 제한 때문에 작게)
MAX_TOKENS = 800
MAX_CARDS = 5
MAX_QUICK_REPLIES = 4
OVERVIEW_CHARS = 200
# FestivalSummary 필드 (카드에는 상세 필드를 넣지 않음)
SUMMARY_KEYS = ("content_id", "title", "start_date", "end_date", "status", "area_code", "area_name",
                "address", "image_url", "lng", "lat", "tags", "is_liked")
TOO_MANY_ROUNDS_TEXT ="질문을 조금 더 구체적으로 알려주시겠어요? 예: '이번 주말 서울에서 하는 음식 축제 알려줘'"


@dataclass
class ChatState:
    db: Session
    liked_ids: frozenset[str] = frozenset()
    profile: dict | None = None
    liked_tags: set[str] | None = None  # 찜한 축제들의 태그 (찜이 없으면 None)
    festivals: dict[str, dict] = field(default_factory=dict)  # 이번 요청에서 Tool이 돌려준 축제 (카드용)
    tool_failed: bool = False


# ---- Tool 실행 ----


def _compact_summary(f: dict) -> dict:
    return {k: f.get(k) for k in ("content_id", "title", "start_date", "end_date", "status", "area_name", "address", "tags")}


def _compact_detail(f: dict) -> dict:
    out = _compact_summary(f) | {k: f.get(k) for k in ("place", "playtime", "fee", "tel", "homepage")}
    out["overview"] = (f.get("overview") or "")[:OVERVIEW_CHARS] or None
    return out


def run_tool(state: ChatState, name: str, arguments: str) -> dict:
    """Tool 1개 실행 → AI에게 보낼 결과 dict. 어떤 실패도 예외로 던지지 않음"""
    try:
        args = json.loads(arguments or "{}")
        if not isinstance(args, dict):
            raise ValueError
    except ValueError:
        return {"ok": False, "error": {"code": "BAD_ARGUMENTS", "message": "Tool 인자가 JSON 객체가 아니에요."}}
    try:
        if name == "search_festivals":
            allowed = ("start_date", "end_date", "area_codes", "tags", "keyword")
            limit = min(int(args.get("limit") or AI_SEARCH_LIMIT), AI_SEARCH_LIMIT)  # 토큰 절약
            result = search_festivals(
                state.db, **{k: v for k, v in args.items() if k in allowed}, limit=limit, liked_ids=state.liked_ids
            )
            if not result["ok"]:
                return result
            for f in result["festivals"]:
                state.festivals[f["content_id"]] = f
            compact = [_compact_summary(f) for f in result["festivals"]]
            if state.profile:
                # 로그인 사용자: 추천 점수(score_festivals와 같은 계산)를 붙여 높은 순으로 → AI가 별도 Tool 호출 없이 고름
                today = today_kst()
                for c, f in zip(compact, result["festivals"]):
                    c["score"] = score_one(f, state.profile, state.liked_tags, today)["score"]
                compact.sort(key=lambda c: -c["score"])
            return {"ok": True, "total": result["total"], "festivals": compact}
        if name == "get_festival_detail":
            result = get_festival_detail(state.db, str(args.get("content_id", "")), liked_ids=state.liked_ids)
            if not result["ok"]:
                return result
            festival = result["festival"]
            state.festivals[festival["content_id"]] = {k: v for k, v in festival.items() if k in SUMMARY_KEYS}
            return {"ok": True, "festival": _compact_detail(festival)}
        return {"ok": False, "error": {"code": "UNKNOWN_TOOL", "message": f"{name} Tool은 없어요."}}
    except TypeError as exc:  # 필수 인자 누락 등
        return {"ok": False, "error": {"code": "BAD_ARGUMENTS", "message": str(exc)}}
    except Exception:  # Tool 내부 오류가 대화 전체를 깨지 않게
        logger.exception("Tool 실행 실패: %s", name)
        state.tool_failed = True
        return {"ok": False, "error": {"code": "TOOL_ERROR", "message": "정보를 가져오지 못했어요."}}


# ---- 최종 답변 → blocks ----


def parse_final(content: str) -> dict:
    """AI 최종 답변 JSON. 형식이 깨졌으면 글 전체를 text로"""
    text = (content or "").strip()
    match = re.search(r"\{.*\}", text, re.S)
    if match:
        try:
            data = json.loads(match.group(0))
            if isinstance(data, dict) and isinstance(data.get("text"), str):
                return data
        except json.JSONDecodeError:
            pass
    return {"intent": "unknown" if not text else "recommend", "text": text or TOO_MANY_ROUNDS_TEXT}


def to_blocks(final: dict, state: ChatState) -> tuple[str, list[dict]]:
    intent = final.get("intent") if final.get("intent") in INTENTS else "recommend"
    blocks: list[dict] = [{"type": "text", "text": final["text"].strip()}]
    if state.tool_failed:
        blocks.append({"type": "text", "text": "일부 정보를 가져오지 못했어요. 잠시 후 다시 물어봐 주세요."})

    reasons = final.get("reasons") if isinstance(final.get("reasons"), dict) else {}
    ids = [str(i) for i in final.get("festival_ids") or [] if str(i) in state.festivals]
    items = [
        {"festival": state.festivals[i], "reason": reasons.get(i) if isinstance(reasons.get(i), str) else None}
        for i in dict.fromkeys(ids)  # 중복 제거, 순서 유지
    ][:MAX_CARDS]
    if items:
        blocks.append({"type": "festival_cards", "items": items})

    options = [
        {"label": str(o["label"])[:30], "message": str(o["message"])[:200]}
        for o in final.get("quick_replies") or []
        if isinstance(o, dict) and o.get("label") and o.get("message")
    ][:MAX_QUICK_REPLIES]
    if options:
        blocks.append({"type": "quick_replies", "options": options})  # 항상 마지막 블록
    return intent, blocks


# ---- 반복 처리 ----


def run_chat(
    db: Session,
    message: str,
    history: list[dict],
    *,
    profile: dict | None = None,
    liked_ids: frozenset[str] = frozenset(),
    context_festival_id: str | None = None,
) -> dict:
    """{"intent", "blocks"}. Groq 실패는 AiError로 올려 보냄 (API에서 502)"""
    state = ChatState(db=db, liked_ids=liked_ids, profile=profile)
    if profile:
        state.liked_tags = liked_tags_of(db, list(liked_ids))
    messages: list[dict] = [
        {"role": "system", "content": prompts.chat_system_prompt(today_kst(), profile, context_festival_id)},
        *({"role": h["role"], "content": h["text"]} for h in history),
        {"role": "user", "content": message},
    ]
    for _ in range(MAX_ROUNDS):
        reply = chat(messages, tools=CHAT_TOOLS, max_tokens=MAX_TOKENS)
        calls = reply.get("tool_calls")
        if not calls:  # final_answer 없이 글로 답한 경우
            intent, blocks = to_blocks(parse_final(reply["content"]), state)
            return {"intent": intent, "blocks": blocks}
        messages.append(reply)
        final = None
        for call in calls:
            name, arguments = call["function"]["name"], call["function"]["arguments"]
            if name == "final_answer":
                final = arguments
                continue
            result = run_tool(state, name, arguments)
            messages.append({"role": "tool", "tool_call_id": call["id"], "content": json.dumps(result, ensure_ascii=False)})
        if final is not None:  # 같은 회차의 다른 Tool을 먼저 실행한 뒤 마무리 (카드에 쓸 축제가 state에 들어가도록)
            intent, blocks = to_blocks(parse_final(final), state)
            return {"intent": intent, "blocks": blocks}
    return {"intent": "unknown", "blocks": [{"type": "text", "text": TOO_MANY_ROUNDS_TEXT}]}
