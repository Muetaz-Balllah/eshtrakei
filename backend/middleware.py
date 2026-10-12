from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.errors import AppError


def _validation_message(exc: RequestValidationError) -> str:
    for error in exc.errors():
        cause = (error.get("ctx") or {}).get("error")
        if cause is not None:
            return str(cause)
    return "تحقق من البيانات المدخلة"


def register_middleware(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"code": "invalid_input", "message": _validation_message(exc)})

    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.code, "message": exc.message},
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(_request: Request, _exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"code": "internal_error", "message": "حدث خطأ غير متوقع"},
        )
