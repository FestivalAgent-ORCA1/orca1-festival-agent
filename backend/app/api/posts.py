from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db  # BE1 담당
from app.core.deps import get_current_user, get_current_user_optional
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.post import CommentCreateRequest, CommentResponse, PostCreateRequest, PostResponse
from app.services import post_service

router = APIRouter(prefix="/api", tags=["community"])


@router.get("/posts", response_model=PageResponse)
def list_posts(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    festival_content_id: str | None = Query(None),
    viewer: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """글 목록 (누구나) — festival_content_id로 특정 축제 글만 거를 수 있음"""
    items, total = post_service.list_posts(db, viewer, page, size, festival_content_id)
    return PageResponse(items=[i.model_dump() for i in items], page=page, size=size, total=total)


@router.post("/posts", response_model=PostResponse, status_code=201)
def create_post(
    body: PostCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """🔒 글쓰기"""
    post = post_service.create_post(db, user, body.title, body.content, body.festival_content_id)
    return post_service.to_post_response(db, post, user)


@router.get("/posts/{post_id}", response_model=PostResponse)
def get_post(
    post_id: int,
    viewer: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """글 상세 (누구나) — 조회수 +1"""
    post = post_service.get_post(db, post_id)
    return post_service.to_post_response(db, post, viewer)


@router.put("/posts/{post_id}", response_model=PostResponse)
def update_post(
    post_id: int,
    body: PostCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """🔒 수정 (작성자만)"""
    post = post_service.update_post(db, user, post_id, body.title, body.content, body.festival_content_id)
    return post_service.to_post_response(db, post, user)


@router.delete("/posts/{post_id}", status_code=204)
def delete_post(
    post_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """🔒 삭제 (작성자만)"""
    post_service.delete_post(db, user, post_id)


@router.get("/posts/{post_id}/comments", response_model=list[CommentResponse])
def list_comments(
    post_id: int,
    viewer: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """댓글 목록 (누구나, 오래된 순)"""
    return post_service.list_comments(db, viewer, post_id)


@router.post("/posts/{post_id}/comments", response_model=CommentResponse, status_code=201)
def create_comment(
    post_id: int,
    body: CommentCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """🔒 댓글 쓰기"""
    comment = post_service.create_comment(db, user, post_id, body.content)
    return CommentResponse(
        id=comment.id, content=comment.content,
        author={"id": user.id, "nickname": user.nickname},
        is_mine=True, created_at=comment.created_at,
    )


@router.delete("/comments/{comment_id}", status_code=204)
def delete_comment(
    comment_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """🔒 댓글 삭제 (작성자만)"""
    post_service.delete_comment(db, user, comment_id)