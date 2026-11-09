from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.db import get_db  # BE1 담당: DB 연결 세션을 주는 함수
from app.core.errors import AppError
from app.core.security import decode_access_token
from app.models.user import User

_bearer = HTTPBearer(auto_error=False)  # Authorization: Bearer <토큰> 헤더 읽기


def get_current_user(
    cred: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """🔒 API용: 토큰이 없거나 틀리면 401"""
    if cred is None:
        raise AppError(401, "UNAUTHORIZED", "로그인이 필요해요.")
    user_id = decode_access_token(cred.credentials)
    if user_id is None:
        raise AppError(401, "UNAUTHORIZED", "로그인이 만료됐어요. 다시 로그인해 주세요.")
    user = db.get(User, user_id)
    if user is None:
        raise AppError(401, "UNAUTHORIZED", "존재하지 않는 사용자예요.")
    return user


def get_current_user_optional(
    cred: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User | None:
    """🔓 API용: 로그인 안 했으면 None (is_liked 같은 개인 정보만 비움)"""
    if cred is None:
        return None
    user_id = decode_access_token(cred.credentials)
    if user_id is None:
        return None
    return db.get(User, user_id)