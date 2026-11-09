from pydantic import BaseModel


class PageResponse(BaseModel):
    """api-spec.md '목록 응답' 공통 형식 — 찜·커뮤니티·알림 목록에서 재사용"""
    items: list
    page: int
    size: int
    total: int