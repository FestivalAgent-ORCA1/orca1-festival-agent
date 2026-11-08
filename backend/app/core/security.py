from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import settings  # BE1 담당. SECRET_KEY가 여기 정의되어야 함

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24  # api-spec.md: 토큰 유효기간 24시간


def hash_password(password: str) -> str:
    """비밀번호 원문 → bcrypt 해시. 원문은 절대 저장·로그 출력 금지 (db-schema.md)"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """로그인 시 입력한 비밀번호가 저장된 해시와 일치하는지 확인"""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(user_id: int) -> str:
    """로그인 성공 시 발급하는 토큰. 안에 사용자 id와 만료 시각이 들어감"""
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> int | None:
    """토큰 → 사용자 id. 만료됐거나 위조된 토큰이면 None"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None