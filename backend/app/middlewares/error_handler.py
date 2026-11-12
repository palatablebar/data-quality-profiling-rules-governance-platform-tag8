"""Uniform error envelope + request id.

Mounted outermost: AppError -> {code,message,detail,request_id}; validation
errors -> QUAL-2007; anything unexpected -> QUAL-5000 with a logged traceback.
"""
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.constants.error_codes import AppError
from app.schemas.common import error_envelope
from app.utils.logger import log_event


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:16]
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content=error_envelope(exc.code, exc.message, _request_id(request), exc.detail),
            headers={"X-Request-ID": _request_id(request) or ""},
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=error_envelope(
                "QUAL-2007",
                "请求参数校验未通过",
                _request_id(request),
                {"errors": [str(item.get("msg")) for item in exc.errors()][:10]},
            ),
            headers={"X-Request-ID": _request_id(request) or ""},
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception):
        log_event("RUN_FAILED", run_id="-", error_code="QUAL-5000", reason=f"{type(exc).__name__}: {exc}")
        return JSONResponse(
            status_code=500,
            content=error_envelope("QUAL-5000", "服务内部错误", _request_id(request)),
            headers={"X-Request-ID": _request_id(request) or ""},
        )
