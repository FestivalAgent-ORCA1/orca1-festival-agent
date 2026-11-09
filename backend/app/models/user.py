from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, ForeignKey, String, func,
)

from app.core.db import Base  # BE1이 db.py에 정의할 공통 부품 (아직 없음 → BE1에 요청)


class User(Base):
    """users — 회원 (db-schema.md 기준)"""
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)        # 로그인 ID
    password_hash = Column(String(255), nullable=False)             # bcrypt 해시만 저장
    nickname = Column(String(30), nullable=False)
    age_group = Column(String(10), nullable=True)                   # 온보딩 전에는 NULL
    onboarded = Column(Boolean, nullable=False, default=False)      # 첫 설정 완료 여부
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class UserRegion(Base):
    """user_regions — 선호 지역 (사용자당 0~3개)"""
    __tablename__ = "user_regions"

    # 두 컬럼을 합쳐서 PK → 같은 사용자가 같은 지역을 중복 등록 못 함
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    area_code = Column(String(5), primary_key=True)                 # tags.md 지역 코드


class UserTag(Base):
    """user_tags — 관심사 (사용자당 1~5개)"""
    __tablename__ = "user_tags"

    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    tag_code = Column(String(20), primary_key=True)                 # tags.md 태그 코드