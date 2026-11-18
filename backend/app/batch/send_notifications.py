"""찜 알림 만들기 (docs/workflow.md '찜 알림', 담당 BE2) — 매일 09:00

각 사용자의 찜한 축제마다:
  시작 7일 전              → FESTIVAL_D7       "찜한 '{축제명}'가 일주일 뒤 시작해요"
  시작 1일 전              → FESTIVAL_D1       "찜한 '{축제명}'가 내일 시작해요!"
  시작 당일                → FESTIVAL_START    "'{축제명}'가 오늘 시작했어요"
  찜한 축제가 끝난 다음 날 → SIMILAR_FESTIVAL  similar_festivals()로 1개 골라 추천

- 같은 알림이 두 번 생기지 않도록: 만들기 전에 이미 있는지 확인 + DB UNIQUE(user_id, type, festival_content_id)
- 오늘 실행을 놓친 경우를 대비해 "그 날짜와 정확히 같을 때"만 만든다 (지난 알림을 몰아서 보내지 않음)

직접 실행 (backend/에서, 공용 DB에 쓰므로 주의):
    python -m app.batch.send_notifications                  # 오늘 기준
    python -m app.batch.send_notifications --date 2026-11-20 # 특정 날짜 기준 (테스트용)
"""

import argparse
import logging
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models.festival import Festival
from app.models.like import Like
from app.models.notification import Notification
from app.services.festival_service import similar_festivals, today_kst

logger = logging.getLogger(__name__)

D7, D1, START, SIMILAR = "FESTIVAL_D7", "FESTIVAL_D1", "FESTIVAL_START", "SIMILAR_FESTIVAL"


def _exists(db: Session, user_id: int, type_: str, content_id: str) -> bool:
    return db.scalar(
        select(Notification.id).where(
            Notification.user_id == user_id,
            Notification.type == type_,
            Notification.festival_content_id == content_id,
        )
    ) is not None


def _create(db: Session, user_id: int, type_: str, content_id: str, message: str) -> bool:
    """알림 1개 만들기. 이미 있으면 False (UNIQUE 제약과 같은 기준)"""
    if _exists(db, user_id, type_, content_id):
        return False
    db.add(Notification(user_id=user_id, type=type_, festival_content_id=content_id, message=message[:300]))
    try:
        db.commit()
    except IntegrityError:  # 동시에 두 번 돌아도 DB UNIQUE가 막아줌
        db.rollback()
        return False
    return True


def _pick_similar(db: Session, user_id: int, ended: Festival, liked_ids: set[str]) -> dict | None:
    """끝난 축제와 비슷한 축제 중, 아직 찜 안 했고 이미 추천하지 않은 것 1개"""
    for candidate in similar_festivals(db, ended.content_id, liked_ids=liked_ids):
        cid = candidate["content_id"]
        if cid in liked_ids or _exists(db, user_id, SIMILAR, cid):
            continue
        return candidate
    return None


def send_notifications(db: Session, today: date | None = None) -> dict:
    """오늘 보내야 할 찜 알림을 만들고, 종류별 생성 개수를 돌려준다"""
    today = today or today_kst()
    counts = {D7: 0, D1: 0, START: 0, SIMILAR: 0}

    rows = db.execute(
        select(Like.user_id, Festival)
        .join(Festival, Festival.content_id == Like.content_id)
        .order_by(Like.user_id, Festival.start_date)
    ).all()

    liked_by_user: dict[int, set[str]] = {}
    for user_id, festival in rows:
        liked_by_user.setdefault(user_id, set()).add(festival.content_id)

    for user_id, f in rows:
        title = f.title
        if f.start_date == today + timedelta(days=7):
            counts[D7] += _create(db, user_id, D7, f.content_id, f"찜한 '{title}'가 일주일 뒤 시작해요")
        elif f.start_date == today + timedelta(days=1):
            counts[D1] += _create(db, user_id, D1, f.content_id, f"찜한 '{title}'가 내일 시작해요!")
        elif f.start_date == today:
            counts[START] += _create(db, user_id, START, f.content_id, f"'{title}'가 오늘 시작했어요")

        if f.end_date == today - timedelta(days=1):
            pick = _pick_similar(db, user_id, f, liked_by_user[user_id])
            if pick:
                message = f"'{title}'가 끝났어요. 비슷한 '{pick['title']}'는 어때요?"
                counts[SIMILAR] += _create(db, user_id, SIMILAR, pick["content_id"], message)

    logger.info("찜 알림 생성 %s (기준일 %s)", counts, today)
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="찜 알림 만들기")
    parser.add_argument("--date", type=date.fromisoformat, default=None, help="기준 날짜 YYYY-MM-DD (기본: 오늘)")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    with SessionLocal() as db:
        print(send_notifications(db, today=args.date))


if __name__ == "__main__":
    main()