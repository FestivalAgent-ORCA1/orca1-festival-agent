from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db  # BE1 담당
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.notification import UnreadCountResponse
from app.services import notification_service

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("", response_model=PageResponse)
def list_notifications(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """🔒 알림 목록 (최신 순)"""
    items, total = notification_service.list_notifications(db, user, page, size)
    return PageResponse(items=[i.model_dump() for i in items], page=page, size=size, total=total)


@router.get("/unread-count", response_model=UnreadCountResponse)
def get_unread_count(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """🔒 안 읽은 알림 수 — 헤더 배지용"""
    return UnreadCountResponse(count=notification_service.unread_count(db, user))


@router.patch("/read-all", status_code=204)
def mark_all_read(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """🔒 모두 읽음"""
    notification_service.mark_all_read(db, user)


@router.patch("/{notification_id}/read", status_code=204)
def mark_read(
    notification_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """🔒 읽음 처리"""
    notification_service.mark_read(db, user, notification_id)