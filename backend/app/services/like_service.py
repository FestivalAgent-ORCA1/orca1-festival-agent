from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.like import Like
from app.models.user import User


def add_like(db: Session, user: User, content_id: str) -> Like:
    exists = db.scalar(select(Like).where(Like.user_id == user.id, Like.content_id == content_id))
    if exists:
        raise AppError(409, "ALREADY_LIKED", "이미 찜한 축제예요.")
    # TODO(BE1 연동): 존재하지 않는 축제면 404 FESTIVAL_NOT_FOUND — festival 조회 함수 생기면 추가
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


def list_liked_ids(db: Session, user: User) -> list[str]:
    """찜한 축제 ID 목록 — BE1의 추천 로직(점수 계산)에서도 사용 (주차 계획의 list_liked_ids)"""
    rows = db.scalars(
        select(Like.content_id).where(Like.user_id == user.id).order_by(Like.created_at.desc())
    )
    return list(rows)


def list_likes(db: Session, user: User, page: int, size: int) -> tuple[list, int]:
    """내 찜 목록 (페이지네이션). items는 아직 content_id만 —
    TODO(BE1 연동): festivals 테이블·FestivalSummary 완성되면 축제 카드 모양으로 교체
    """
    total = db.scalar(select(func.count()).select_from(Like).where(Like.user_id == user.id))
    rows = db.scalars(
        select(Like)
        .where(Like.user_id == user.id)
        .order_by(Like.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    items = [{"content_id": like.content_id} for like in rows]  # ← TODO: FestivalSummary로 교체
    return items, total