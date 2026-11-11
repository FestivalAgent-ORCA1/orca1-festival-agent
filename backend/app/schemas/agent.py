"""POST /api/agent/chat 요청·응답 (docs/agent-response-format.md)"""

from typing import Any, Literal

from pydantic import BaseModel, Field

MAX_HISTORY = 10


class HistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    text: str = Field(max_length=2000)


class ChatContext(BaseModel):
    festival_content_id: str | None = None
    itinerary: dict[str, Any] | None = None  # 화면의 마지막 시간표 (일정 수정용, 2주차 확정)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    history: list[HistoryItem] = Field(default_factory=list)
    context: ChatContext = Field(default_factory=ChatContext)


class ChatResponse(BaseModel):
    intent: Literal["recommend", "festival_info", "itinerary", "smalltalk", "unknown"]
    blocks: list[dict[str, Any]]  # type별 모양은 agent-response-format.md (프론트는 모르는 type 무시)
