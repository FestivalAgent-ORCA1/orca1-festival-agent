from pydantic import BaseModel


class LikeCreateRequest(BaseModel):
    content_id: str  # 축제 ID (문자열 — db-schema.md 공통 규칙)