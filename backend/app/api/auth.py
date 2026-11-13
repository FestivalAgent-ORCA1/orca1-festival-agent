from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db  # BE1 담당
from app.core.security import create_access_token
from app.schemas.user import AuthResponse, LoginRequest, SignupRequest
from app.services import user_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup", response_model=AuthResponse, status_code=201)
def signup(body: SignupRequest, db: Session = Depends(get_db)):
    """회원가입 — 가입과 동시에 로그인 처리 (api-spec)"""
    user = user_service.signup(db, body.email, body.password, body.nickname)
    return AuthResponse(
        access_token=create_access_token(user.id),
        user=user_service.to_user_response(db, user),
    )


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = user_service.login(db, body.email, body.password)
    return AuthResponse(
        access_token=create_access_token(user.id),
        user=user_service.to_user_response(db, user),
    )