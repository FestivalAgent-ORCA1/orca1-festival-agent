from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationResponse


def list_notifications(db: Session, user: User, page: int, size: int) -> tuple[list, int]:
    total = db.scalar(
        select(func.count()).select_from(Notification).where(Notification.user_id == user.id)
    )
    rows = db.scalars(
        select(Notification)
        .where(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())      # 최신 순 (api-spec)
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    items = [
        NotificationResponse(
            id=n.id, type=n.type, message=n.message,
            festival_content_id=n.festival_content_id,
            is_read=n.is_read, created_at=n.created_at,
        )
        for n in rows
    ]
    return items, total


def unread_count(db: Session, user: User) -> int:
    return db.scalar(
        select(func.count()).select_from(Notification)
        .where(Notification.user_id == user.id, Notification.is_read == False)  # noqa: E712
    )


def mark_read(db: Session, user: User, notification_id: int) -> None:
    notification = db.get(Notification, notification_id)
    if notification is None or notification.user_id != user.id:
        raise AppError(404, "NOTIFICATION_NOT_FOUND", "알림을 찾을 수 없어요.")
    notification.is_read = True
    db.commit()


def mark_all_read(db: Session, user: User) -> None:
    db.query(Notification).filter(
        Notification.user_id == user.id, Notification.is_read == False  # noqa: E712
    ).update({"is_read": True})
    db.commit()