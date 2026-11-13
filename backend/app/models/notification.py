from sqlalchemy import Boolean, BigInteger, Column, DateTime, ForeignKey, String, UniqueConstraint, func

from app.core.db import Base


class Notification(Base):
    """notifications — 알림 (batch/send_notifications.py가 매일 생성)"""
    __tablename__ = "notifications"
    __table_args__ = (
        # 배치가 두 번 돌아도 같은 알림이 중복 생성되지 않게
        UniqueConstraint("user_id", "type", "festival_content_id", name="uq_notifications_user_type_festival"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(30), nullable=False)            # FESTIVAL_D7 / FESTIVAL_D1 / FESTIVAL_START / SIMILAR_FESTIVAL
    festival_content_id = Column(String(20), ForeignKey("festivals.content_id"), nullable=True)
    message = Column(String(300), nullable=False)
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())