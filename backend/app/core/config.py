"""환경 변수(.env) 읽기. 값은 backend/.env 또는 서버(Render)의 환경 변수에서 가져온다."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]  # backend/


class Settings(BaseSettings):
    # extra="ignore": .env에 여기 없는 키가 있어도 시작할 때 오류를 내지 않음
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    # DB
    DATABASE_URL: str
    DB_SSL_CA: str = ""  # Aiven 인증서 경로. 상대 경로면 backend/ 기준

    # 로그인 (BE2 core/security.py에서 사용)
    SECRET_KEY: str

    # 서버
    CORS_ORIGINS: str = "http://localhost:5173"  # 쉼표로 여러 개
    ENABLE_SCHEDULER: bool = False  # 자동 실행 작업은 한 곳에서만 켠다

    # 외부 API
    TOURAPI_SERVICE_KEY: str = ""
    KAKAO_REST_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = ""

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip().rstrip("/") for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def ssl_ca_path(self) -> str:
        if not self.DB_SSL_CA:
            return ""
        path = Path(self.DB_SSL_CA)
        return str(path if path.is_absolute() else BACKEND_DIR / path)


settings = Settings()
