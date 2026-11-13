from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    email: EmailStr                                      # 이메일 형식 자동 검증
    password: str = Field(min_length=8)                  # api-spec: 8자 이상
    nickname: str = Field(min_length=2, max_length=15)   # api-spec: 2~15자


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UpdateMeRequest(BaseModel):
    nickname: str = Field(min_length=2, max_length=15)


class PreferencesRequest(BaseModel):
    age_group: str
    regions: list[str] = Field(max_length=3)             # 0~3개
    tags: list[str] = Field(min_length=1, max_length=5)  # 1~5개


class UserResponse(BaseModel):
    """api-spec.md 'User (내 정보)' 모양"""
    id: int
    email: str
    nickname: str
    age_group: str | None
    regions: list[str]
    tags: list[str]
    onboarded: bool
    created_at: datetime


class AuthResponse(BaseModel):
    """회원가입·로그인 응답"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse