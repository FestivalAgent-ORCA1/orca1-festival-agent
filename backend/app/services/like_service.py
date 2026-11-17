from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.like import Like
from app.models.user import User
from app.services import festival_service  # BE1: 축제 조회·FestivalSummary 변환


def add_like(db: Session, user: User, content_id: str) -> Like:
    festival_service.get_festival_or_404(db, content_id)  # 없는 축제면 404 FESTIVAL_NOT_FOUND
    exists = db.scalar(select(Like).where(Like.user_id == user.id, Like.content_id == content_id))
    if exists:
        raise AppError(409, "ALREADY_LIKED", "이미 찜한 축제예요.")
    like = Like(user_id=user.id, content_id=content_id)
    db.add(like)
    db.commit()
    return like


def remove_like(db: Session, user: User, content_id: str) -> None:
    like = db.scalar(select(Like).where(Like.user_id == user.id, Like.content_id == content_id))
    if like is None:
        raise AppError(404, "LIKE_NOT_FOUND", "찜하지 않은 축제예요.")
    db.delete(like)
    db.commit()


def list_liked_ids(db: Session, user: User | None) -> list[str]:
    """찜한 축제 ID 목록 (최근 찜한 순). 로그인 안 했으면 빈 목록.
    BE1의 추천·축제 목록(is_liked 표시)에서도 사용
    """
    if user is None:
        return []
    rows = db.scalars(
        select(Like.content_id).where(Like.user_id == user.id).order_by(Like.created_at.desc())
    )
    return list(rows)


def list_likes(db: Session, user: User, page: int, size: int) -> tuple[list[dict], int]:
    """내 찜 목록 (페이지네이션). items = FestivalSummary (api-spec 8번)"""
    total = db.scalar(select(func.count()).select_from(Like).where(Like.user_id == user.id))
    content_ids = list(
        db.scalars(
            select(Like.content_id)
            .where(Like.user_id == user.id)
            .order_by(Like.created_at.desc(), Like.id.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
    )
    # 찜 목록이므로 전부 is_liked = true
    items = festival_service.summaries_by_ids(db, content_ids, liked_ids=set(content_ids))
    return items, total