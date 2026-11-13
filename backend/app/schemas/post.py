from datetime import datetime

from pydantic import BaseModel, Field


class AuthorResponse(BaseModel):
    id: int
    nickname: str


class PostCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)
    festival_content_id: str | None = None   # 관련 축제 (선택)


class PostResponse(BaseModel):
    """글 (목록 항목 / 상세 공통) — api-spec 10번"""
    id: int
    title: str
    content: str                              # 목록에서는 앞 100자만 (service에서 자름)
    author: AuthorResponse
    festival: dict | None = None               # TODO(BE1 연동): {content_id, title}
    view_count: int
    comment_count: int
    is_mine: bool
    created_at: datetime
    updated_at: datetime


class CommentCreateRequest(BaseModel):
    content: str = Field(min_length=1, max_length=1000)


class CommentResponse(BaseModel):
    id: int
    content: str
    author: AuthorResponse
    is_mine: bool
    created_at: datetime