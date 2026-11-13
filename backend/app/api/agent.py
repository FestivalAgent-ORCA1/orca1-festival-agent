"""/api/agent/chat — AI 채팅 (docs/agent-response-format.md, docs/workflow.md)"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agent.client import AiError
from app.agent.intent import classify_by_rules
from app.agent.itinerary_chat import run_itinerary_chat
from app.agent.loop import run_chat
from app.core.db import get_db
from app.core.deps import get_current_user_optional
from app.core.errors import AppError
from app.models.user import User
from app.schemas.agent import MAX_HISTORY, ChatRequest, ChatResponse
from app.services.like_service import list_liked_ids
from app.services.recommend_service import get_profile

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/chat", response_model=ChatResponse)
def chat(
    body: ChatRequest,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
):
    """🔓 일정 요청(키워드 규칙)은 itinerary_chat, 나머지는 AI 반복 처리. Groq 실패는 502"""
    context = body.context.model_dump()
    history = [h.model_dump() for h in body.history[-MAX_HISTORY:]]
    try:
        if classify_by_rules(body.message, context) == "itinerary":
            return run_itinerary_chat(db, body.message, history, context)
        return run_chat(
            db,
            body.message,
            history,
            profile=get_profile(db, user),
            liked_ids=frozenset(list_liked_ids(db, user)) if user else frozenset(),
            context_festival_id=body.context.festival_content_id,
        )
    except AiError as exc:
        raise AppError(502, "EXTERNAL_API_ERROR", exc.message) from exc
