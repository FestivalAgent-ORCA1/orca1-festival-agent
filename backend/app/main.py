"""서버 시작 파일. 실행: backend/에서 `uvicorn app.main:app --reload`"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

import app.models  # noqa: F401  모든 모델을 먼저 불러와 테이블 관계(FK)를 확정
from app.api import agent, auth, festivals, itinerary, likes, meta, notifications, places, posts, schedules, users
from app.core.config import settings
from app.core.errors import AppError, app_error_handler

logger = logging.getLogger("app")

app = FastAPI(title="Festival Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,  # 토큰은 Authorization 헤더로 보내서 쿠키가 필요 없음
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


# ---- 오류 응답을 api-spec.md 형식({code, message})으로 통일 ----

app.add_exception_handler(AppError, app_error_handler)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    first = exc.errors()[0] if exc.errors() else {}
    field = ".".join(str(p) for p in first.get("loc", [])[1:]) or "요청"
    return JSONResponse(
        status_code=422,
        content={"code": "VALIDATION_ERROR", "message": f"{field} 값을 확인해 주세요."},
    )


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request: Request, exc: StarletteHTTPException):
    codes = {401: "UNAUTHORIZED", 403: "FORBIDDEN", 404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}
    message = exc.detail if isinstance(exc.detail, str) else "요청을 처리하지 못했어요."
    if exc.status_code == 404 and message == "Not Found":
        message = "요청한 주소를 찾을 수 없어요."
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": codes.get(exc.status_code, "HTTP_ERROR"), "message": message},
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(Exception)
async def internal_error_handler(request: Request, exc: Exception):
    logger.exception("처리하지 못한 오류: %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"code": "INTERNAL_ERROR", "message": "서버에 문제가 생겼어요. 잠시 후 다시 시도해 주세요."},
    )


# ---- 라우터 ----
# BE1
app.include_router(meta.router)
app.include_router(festivals.router)
app.include_router(places.router)
app.include_router(itinerary.router)
app.include_router(agent.router)
# BE2
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(likes.router)
app.include_router(schedules.router)
app.include_router(posts.router)
app.include_router(notifications.router)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
