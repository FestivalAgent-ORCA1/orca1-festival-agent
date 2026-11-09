from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String, UniqueConstraint, func

from app.core.db import Base


class Like(Base):
    """likes — 찜"""
    __tablename__ = "likes"
    __table_args__ = (
        # 같은 사용자가 같은 축제를 두 번 찜하지 못하게
        UniqueConstraint("user_id", "content_id", name="uq_likes_user_content"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content_id = Column(String(20), ForeignKey("festivals.content_id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())