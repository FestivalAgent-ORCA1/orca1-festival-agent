"""테스트는 공용 DB를 쓰지 않고 메모리 SQLite로 실행한다.

실행: backend/에서 `.venv\\Scripts\\python -m pytest`
"""

import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import BigInteger, create_engine  # noqa: E402
from sqlalchemy.ext.compiler import compiles  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

import app.models  # noqa: E402,F401
from app.core.db import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402


@compiles(BigInteger, "sqlite")
def _bigint_as_integer(type_, compiler, **kw):
    """SQLite는 INTEGER PK만 자동 증가하므로 테스트에서만 BIGINT → INTEGER (MySQL은 그대로)"""
    return "INTEGER"


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = Session()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()
