from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db  # BE1 담당
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.schedule import ScheduleCreateRequest, ScheduleDetailResponse
from app.services import schedule_service

router = APIRouter(prefix="/api/schedules", tags=["schedules"])


@router.get("", response_model=PageResponse)
def list_schedules(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """🔒 내 일정 목록"""
    items, total = schedule_service.list_schedules(db, user, page, size)
    return PageResponse(items=[i.model_dump() for i in items], page=page, size=size, total=total)


@router.post("", response_model=ScheduleDetailResponse, status_code=201)
def create_schedule(
    body: ScheduleCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """🔒 일정 저장"""
    schedule = schedule_service.create_schedule(db, user, body)
    return schedule_service.to_detail_response(db, schedule)


@router.get("/{schedule_id}", response_model=ScheduleDetailResponse)
def get_schedule(
    schedule_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """🔒 일정 상세"""
    schedule = schedule_service.get_schedule(db, user, schedule_id)
    return schedule_service.to_detail_response(db, schedule)


@router.put("/{schedule_id}", response_model=ScheduleDetailResponse)
def update_schedule(
    schedule_id: int,
    body: ScheduleCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """🔒 일정 수정 — 다시 계산한 결과로 전체 교체"""
    schedule = schedule_service.update_schedule(db, user, schedule_id, body)
    return schedule_service.to_detail_response(db, schedule)


@router.delete("/{schedule_id}", status_code=204)
def delete_schedule(
    schedule_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """🔒 일정 삭제"""
    schedule_service.delete_schedule(db, user, schedule_id)