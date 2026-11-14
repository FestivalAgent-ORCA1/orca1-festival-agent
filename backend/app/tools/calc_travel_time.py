"""Tool: calc_travel_time — 이웃한 두 장소 사이 자동차 이동 시간 (docs/tool-spec.md 4번)

순서: DB 캐시(travel_times, 30일 이내) → 없으면 카카오 길찾기 → 결과를 DB에 저장
카카오가 실패하면 직선거리 × 1.4 ÷ 시속 30km (최소 5분)로 추정하고 source="estimate"
"""

import logging
import math
from datetime import datetime, timedelta
from decimal import Decimal

import httpx
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models.festival import TravelTime
from app.services.festival_service import KST
from app.tools import kakao_client

logger = logging.getLogger(__name__)

CACHE_DAYS = 30
ROAD_FACTOR = 1.4  # 직선거리 → 도로 거리 보정
ESTIMATE_KMH = 30
MIN_ESTIMATE_MIN = 5
NEAR_METERS = 50  # 이보다 가까우면 카카오를 부르지 않고 걸어서 이동으로 봄 (카카오는 5m 이내면 오류)


def _now() -> datetime:
    return datetime.now(KST).replace(tzinfo=None)


def straight_km(from_lng: float, from_lat: float, to_lng: float, to_lat: float) -> float:
    """두 좌표 사이 직선거리 (km, 하버사인)"""
    r = 6371.0
    p1, p2 = math.radians(from_lat), math.radians(to_lat)
    dp, dl = p2 - p1, math.radians(to_lng - from_lng)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def estimate(from_lng: float, from_lat: float, to_lng: float, to_lat: float) -> tuple[int, float]:
    """(분, km) 추정값. build_timeline도 직선거리 배치에 사용"""
    km = straight_km(from_lng, from_lat, to_lng, to_lat) * ROAD_FACTOR
    return max(MIN_ESTIMATE_MIN, math.ceil(km / ESTIMATE_KMH * 60)), round(km, 2)


def _point(value) -> tuple[str, float, float]:
    content_id = str(value["content_id"])
    return content_id, float(value["lng"]), float(value["lat"])


def _leg(from_id: str, to_id: str, minutes: int, km: float, source: str) -> dict:
    return {"from_content_id": from_id, "to_content_id": to_id,
            "duration_min": int(minutes), "distance_km": round(float(km), 2), "source": source}


def _cached(db: Session, from_id: str, to_id: str) -> TravelTime | None:
    row = db.get(TravelTime, (from_id, to_id))
    if row and row.created_at and row.created_at >= _now() - timedelta(days=CACHE_DAYS):
        return row
    return None


def _save(db: Session, from_id: str, to_id: str, minutes: int, km: float) -> None:
    try:
        row = db.get(TravelTime, (from_id, to_id)) or TravelTime(from_content_id=from_id, to_content_id=to_id)
        row.duration_min = minutes
        row.distance_km = Decimal(str(round(km, 2)))
        row.created_at = _now()
        db.add(row)
        db.commit()
    except Exception as exc:  # 캐시 저장 실패는 결과에 영향 없음
        db.rollback()
        logger.warning("travel_times 저장 실패 %s→%s: %s", from_id, to_id, exc)


def compute_legs(db: Session, legs: list[dict], *, client: httpx.Client | None = None) -> list[dict]:
    """서비스(itinerary_service)에서 쓰는 본체. 각 leg마다 cache → kakao → estimate"""
    results = []
    for leg in legs:
        from_id, from_lng, from_lat = _point(leg["from"])
        to_id, to_lng, to_lat = _point(leg["to"])
        if from_id == to_id:
            results.append(_leg(from_id, to_id, 0, 0, "cache"))
            continue
        if row := _cached(db, from_id, to_id):
            results.append(_leg(from_id, to_id, row.duration_min, row.distance_km, "cache"))
            continue
        if straight_km(from_lng, from_lat, to_lng, to_lat) * 1000 < NEAR_METERS:
            results.append(_leg(from_id, to_id, MIN_ESTIMATE_MIN, 0.05, "estimate"))
            continue
        try:
            seconds, meters = kakao_client.directions(from_lng, from_lat, to_lng, to_lat, client=client)
            minutes, km = max(1, math.ceil(seconds / 60)), meters / 1000
            _save(db, from_id, to_id, minutes, km)
            results.append(_leg(from_id, to_id, minutes, km, "kakao"))
        except kakao_client.KakaoError as exc:
            logger.info("카카오 실패 → 추정 %s→%s: %s", from_id, to_id, exc.code)
            minutes, km = estimate(from_lng, from_lat, to_lng, to_lat)
            results.append(_leg(from_id, to_id, minutes, km, "estimate"))
    return results


def calc_travel_time(legs: list[dict], *, db: Session | None = None) -> dict:
    """AI Tool용: 실패해도 예외 대신 {"ok": False, "error": ...}"""
    try:
        if db is not None:
            return {"ok": True, "legs": compute_legs(db, legs)}
        with SessionLocal() as session:
            return {"ok": True, "legs": compute_legs(session, legs)}
    except (KeyError, TypeError, ValueError):
        return {"ok": False, "error": {"code": "BAD_REQUEST", "message": "장소 좌표(content_id, lng, lat)를 확인해 주세요."}}
