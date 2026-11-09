"""MySQL(Aiven) 연결. 모든 모델은 Base를 상속하고, API는 Depends(get_db)로 세션을 받는다."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

connect_args: dict = {}
engine_options: dict = {}
if settings.DATABASE_URL.startswith("mysql"):
    # 접속할 때마다 한국 시간으로 (db-schema.md: 시간은 모두 한국 시간 기준)
    connect_args["init_command"] = "SET time_zone = '+09:00'"
    if settings.ssl_ca_path:
        connect_args["ssl"] = {"ca": settings.ssl_ca_path}  # Aiven은 SSL 필수
    # 공용 DB 최대 접속이 76개라 작게 잡음 (기본값은 프로세스당 15개)
    engine_options = {"pool_size": 3, "max_overflow": 2, "pool_recycle": 280}

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # 끊긴 연결 자동 재연결 (Aiven은 오래 놀면 연결을 끊음)
    connect_args=connect_args,
    **engine_options,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """모든 모델이 상속하는 부모 클래스"""


def get_db():
    """API 함수에서 Depends(get_db)로 받아서 씀. 요청이 끝나면 자동으로 닫힘"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
