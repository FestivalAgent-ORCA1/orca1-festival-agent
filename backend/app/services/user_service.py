from datetime import timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import AGE_GROUP_CODES, REGION_CODES, TAG_CODES  # BE1: tags.md 코드 목록
from app.core.errors import AppError
from app.core.security import hash_password, verify_password
from app.models.user import User, UserRegion, UserTag
from app.schemas.user import UserResponse

KST = timezone(timedelta(hours=9))  # DB는 한국 시간으로 저장 (db-schema.md)


def to_user_response(db: Session, user: User) -> UserResponse:
    """User 모델 → api-spec 'User' 응답 모양 (선호 지역·관심사 포함)"""
    regions = db.scalars(select(UserRegion.area_code).where(UserRegion.user_id == user.id)).all()
    tags = db.scalars(select(UserTag.tag_code).where(UserTag.user_id == user.id)).all()
    return UserResponse(
        id=user.id,
        email=user.email,
        nickname=user.nickname,
        age_group=user.age_group,
        regions=list(regions),
        tags=list(tags),
        onboarded=user.onboarded,
        created_at=user.created_at.replace(tzinfo=KST),  # "+09:00" 붙여서 응답
    )


def signup(db: Session, email: str, password: str, nickname: str) -> User:
    if db.scalar(select(User).where(User.email == email)):
        raise AppError(409, "EMAIL_DUPLICATED", "이미 가입된 이메일이에요.")
    user = User(email=email, password_hash=hash_password(password), nickname=nickname, onboarded=False)
    db.add(user)
    db.commit()
    db.refresh(user)  # DB가 채운 id, created_at을 다시 읽어옴
    return user


def login(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    # 이메일·비밀번호 중 뭐가 틀렸는지 구분하지 않음 (api-spec, 보안상 이유)
    if user is None or not verify_password(password, user.password_hash):
        raise AppError(401, "INVALID_CREDENTIALS", "이메일 또는 비밀번호가 올바르지 않아요.")
    return user


def update_nickname(db: Session, user: User, nickname: str) -> User:
    user.nickname = nickname
    db.commit()
    db.refresh(user)
    return user


def set_preferences(db: Session, user: User, age_group: str, regions: list[str], tags: list[str]) -> User:
    """첫 설정·관심사 수정 — 전체 교체 방식 (api-spec PUT)"""
    # 목록에 없는 코드면 400 (api-spec 2번)
    if age_group not in AGE_GROUP_CODES:
        raise AppError(400, "BAD_REQUEST", "연령대 값이 올바르지 않아요.")
    if any(code not in REGION_CODES for code in regions):
        raise AppError(400, "BAD_REQUEST", "지역 코드가 올바르지 않아요.")
    if any(code not in TAG_CODES for code in tags):
        raise AppError(400, "BAD_REQUEST", "관심사 코드가 올바르지 않아요.")
    # 같은 코드가 두 번 오면 하나로 (중복 저장 시 DB 오류 방지, 순서는 유지)
    regions = list(dict.fromkeys(regions))
    tags = list(dict.fromkeys(tags))

    db.query(UserRegion).filter(UserRegion.user_id == user.id).delete()
    db.query(UserTag).filter(UserTag.user_id == user.id).delete()
    for code in regions:
        db.add(UserRegion(user_id=user.id, area_code=code))
    for code in tags:
        db.add(UserTag(user_id=user.id, tag_code=code))
    user.age_group = age_group
    user.onboarded = True
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: User) -> None:
    """탈퇴 — 찜·일정·알림 등은 ON DELETE CASCADE로 함께 삭제"""
    db.delete(user)
    db.commit()