"""festivals, festival_tags, travel_times (docs/db-schema.md, 담당 BE1)"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.base import TABLE_ARGS, TimestampMixin


class Festival(TimestampMixin, Base):
    """festivals — 축제 (TourAPI 동기화)"""

    __tablename__ = "festivals"
    __table_args__ = (
        Index("ix_festivals_dates", "start_date", "end_date"),
        TABLE_ARGS,  # 딕셔너리는 튜플의 맨 마지막에
    )

    content_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    area_code: Mapped[str | None] = mapped_column(String(5), index=True)
    sigungu_code: Mapped[str | None] = mapped_column(String(5))
    address: Mapped[str | None] = mapped_column(String(300))
    lng: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    lat: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    image_url: Mapped[str | None] = mapped_column(String(500))
    thumbnail_url: Mapped[str | None] = mapped_column(String(500))
    tel: Mapped[str | None] = mapped_column(String(100))
    overview: Mapped[str | None] = mapped_column(Text)
    homepage: Mapped[str | None] = mapped_column(String(1000))
    place: Mapped[str | None] = mapped_column(String(300))
    playtime: Mapped[str | None] = mapped_column(String(300))
    fee: Mapped[str | None] = mapped_column(String(500))
    tourapi_modified_at: Mapped[datetime | None] = mapped_column(DateTime)
    detail_synced_at: Mapped[datetime | None] = mapped_column(DateTime)

    # festival.tags 로 태그 목록에 접근
    tags: Mapped[list["FestivalTag"]] = relationship(
        back_populates="festival", cascade="all, delete-orphan", lazy="selectin"
    )

    @property
    def tag_codes(self) -> list[str]:
        return sorted(t.tag_code for t in self.tags)


class FestivalTag(Base):
    """festival_tags — 축제 태그 (1~3개)"""

    __tablename__ = "festival_tags"
    __table_args__ = (Index("ix_festival_tags_tag", "tag_code"), TABLE_ARGS)

    content_id: Mapped[str] = mapped_column(
        ForeignKey("festivals.content_id", ondelete="CASCADE"), primary_key=True
    )
    tag_code: Mapped[str] = mapped_column(String(20), primary_key=True)

    festival: Mapped["Festival"] = relationship(back_populates="tags")


class TravelTime(Base):
    """travel_times — 이동 시간 캐시 (방향 있음, 30일 지나면 다시 계산)"""

    __tablename__ = "travel_times"
    __table_args__ = TABLE_ARGS

    from_content_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    to_content_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    duration_min: Mapped[int] = mapped_column(Integer)
    distance_km: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
