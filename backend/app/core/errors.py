from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """서비스 전체 공통 예외. api-spec.md '오류 응답' 형식(code + message)에 맞춤.

    사용 예: raise AppError(409, "EMAIL_DUPLICATED", "이미 가입된 이메일이에요.")
    """

    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """AppError를 api-spec 오류 형식 JSON으로 변환.
    BE1이 main.py에 app.add_exception_handler(AppError, app_error_handler)로 등록 필요.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message},
    )