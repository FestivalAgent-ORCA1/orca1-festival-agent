from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db  # BE1 담당
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.user import PreferencesRequest, UpdateMeRequest, UserResponse
from app.services import user_service

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """🔒 내 정보"""
    return user_service.to_user_response(db, user)


@router.patch("/me", response_model=UserResponse)
def update_me(body: UpdateMeRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """🔒 닉네임 수정"""
    updated = user_service.update_nickname(db, user, body.nickname)
    return user_service.to_user_response(db, updated)


@router.put("/me/preferences", response_model=UserResponse)
def set_preferences(body: PreferencesRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """🔒 첫 설정·관심사 수정 — 완료하면 onboarded가 true로 바뀜"""
    updated = user_service.set_preferences(db, user, body.age_group, body.regions, body.tags)
    return user_service.to_user_response(db, updated)


@router.delete("/me", status_code=204)
def delete_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """🔒 탈퇴"""
    user_service.delete_user(db, user)