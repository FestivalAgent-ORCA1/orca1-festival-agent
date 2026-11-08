from datetime import datetime

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    """api-spec 11번 알림 모양"""
    id: int
    type: str                             # FESTIVAL_D7 / FESTIVAL_D1 / FESTIVAL_START / SIMILAR_FESTIVAL
    message: str
    festival_content_id: str | None
    is_read: bool
    created_at: datetime


class UnreadCountResponse(BaseModel):
    count: int