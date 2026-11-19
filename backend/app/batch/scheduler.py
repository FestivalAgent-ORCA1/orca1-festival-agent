"""자동 실행 작업 등록 (docs/workflow.md '자동 실행 작업', 담당 BE2 · BE1과 함께)

| 작업               | 시각 (한국 시간)   | 담당 |
| sync_festivals     | 매주 월요일 04:00  | BE1  |
| extract_tags       | sync 끝난 직후     | BE1  |
| send_notifications | 매일 09:00         | BE2  |

공용 DB라서 여러 서버에서 동시에 돌면 안 된다 → .env의 ENABLE_SCHEDULER=true 인 서버 한 곳에서만 켠다.

main.py에서 사용 (BE1 파일이라 연결은 BE1과 함께):
    from contextlib import asynccontextmanager
    from app.batch.scheduler import start_scheduler, stop_scheduler

    @asynccontextmanager
    async def lifespan(app):
        start_scheduler()
        yield
        stop_scheduler()

    app = FastAPI(title="Festival Agent API", lifespan=lifespan)
"""

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.core.db import SessionLocal

logger = logging.getLogger(__name__)

TIMEZONE = "Asia/Seoul"
_scheduler: BackgroundScheduler | None = None


def run_weekly_festival_update() -> None:
    """축제 목록 갱신 → 바로 이어서 태그 붙이기 (BE1 작업 두 개를 순서대로)"""
    from app.batch.extract_tags import extract_tags
    from app.batch.sync_festivals import sync_festivals

    with SessionLocal() as db:
        try:
            logger.info("sync_festivals 결과: %s", sync_festivals(db))
        except Exception:
            logger.exception("sync_festivals 실패")
            return  # 갱신이 실패하면 태그 작업도 건너뜀
    with SessionLocal() as db:
        try:
            logger.info("extract_tags 결과: %s", extract_tags(db))
        except Exception:
            logger.exception("extract_tags 실패")


def run_daily_notifications() -> None:
    from app.batch.send_notifications import send_notifications

    with SessionLocal() as db:
        try:
            send_notifications(db)
        except Exception:
            logger.exception("send_notifications 실패")


def start_scheduler() -> BackgroundScheduler | None:
    """ENABLE_SCHEDULER=true 일 때만 시작. 꺼져 있으면 아무것도 하지 않음"""
    global _scheduler
    if not settings.ENABLE_SCHEDULER:
        logger.info("자동 실행 작업 꺼짐 (ENABLE_SCHEDULER=false)")
        return None
    if _scheduler is not None:  # 두 번 시작 방지
        return _scheduler

    scheduler = BackgroundScheduler(timezone=TIMEZONE)
    scheduler.add_job(
        run_weekly_festival_update,
        CronTrigger(day_of_week="mon", hour=4, minute=0, timezone=TIMEZONE),
        id="weekly_festival_update",
        max_instances=1,
        coalesce=True,             # 서버가 자다 깨서 밀린 실행이 여러 번 쌓여도 한 번만
        misfire_grace_time=60 * 60,  # 정각을 놓쳐도 1시간 안에 깨어나면 실행
    )
    scheduler.add_job(
        run_daily_notifications,
        CronTrigger(hour=9, minute=0, timezone=TIMEZONE),
        id="daily_notifications",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=60 * 60,
    )
    scheduler.start()
    _scheduler = scheduler
    logger.info("자동 실행 작업 시작: %s", [job.id for job in scheduler.get_jobs()])
    return scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None