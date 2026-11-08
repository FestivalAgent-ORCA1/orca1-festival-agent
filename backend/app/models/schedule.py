from sqlalchemy import (
    DECIMAL, BigInteger, Column, Date, DateTime, ForeignKey, Integer,
    String, Time, UniqueConstraint, func,
)

from app.core.db import Base


class Schedule(Base):
    """schedules — 저장한 일정"""
    __tablename__ = "schedules"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    festival_content_id = Column(String(20), ForeignKey("festivals.content_id"), nullable=False)  # 중심 축제
    title = Column(String(100), nullable=False)          # 기본값 "{축제명} 일정"은 API 쪽에서 처리
    visit_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    total_travel_min = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class ScheduleItem(Base):
    """schedule_items — 일정 안의 장소 (시간표 한 줄)"""
    __tablename__ = "schedule_items"
    __table_args__ = (
        UniqueConstraint("schedule_id", "seq", name="uq_schedule_items_schedule_seq"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    schedule_id = Column(BigInteger, ForeignKey("schedules.id", ondelete="CASCADE"), nullable=False)
    seq = Column(Integer, nullable=False)                # 방문 순서 (1부터)
    category = Column(String(20), nullable=False)        # festival / attraction / restaurant / cafe
    content_id = Column(String(20), nullable=True)       # 사용자가 직접 넣은 장소면 NULL
    name = Column(String(200), nullable=False)
    address = Column(String(300), nullable=True)
    lng = Column(DECIMAL(10, 7), nullable=True)
    lat = Column(DECIMAL(10, 7), nullable=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    travel_min_from_prev = Column(Integer, nullable=True)      # 첫 장소는 NULL
    distance_km_from_prev = Column(DECIMAL(6, 2), nullable=True)
    memo = Column(String(300), nullable=True)