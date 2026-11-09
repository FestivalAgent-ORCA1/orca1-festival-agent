from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db  # BE1 담당
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.like import LikeCreateRequest
from app.services import like_service

router = APIRouter(prefix="/api/likes", tags=["likes"])


@router.get("", response_model=PageResponse)
def list_likes(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),  # api-spec: size 최대 50
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """🔒 내 찜 목록"""
    items, total = like_service.list_likes(db, user, page, size)
    return PageResponse(items=items, page=page, size=size, total=total)


@router.post("", status_code=201)
def add_like(
    body: LikeCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """🔒 찜하기 — 이미 찜했으면 409 ALREADY_LIKED"""
    like_service.add_like(db, user, body.content_id)
    return {"content_id": body.content_id}


@router.delete("/{content_id}", status_code=204)
def remove_like(
    content_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """🔒 찜 취소"""
    like_service.remove_like(db, user, content_id)