"""Bearer-token middleware + the current-user dependency.

The token carries the role for fast checks, but every request re-reads
``users.role`` from MySQL: the database is authoritative.
"""
from fastapi import Depends, Request
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config.database import get_db
from app.constants.error_codes import AppError, ErrorCode
from app.models import User
from app.schemas.common import error_envelope
from app.services import auth_service
from app.utils.jwt import TokenError, decode_access_token

PUBLIC_PATHS = {"/health", "/auth/login", "/openapi.json", "/docs", "/redoc"}
PUBLIC_PREFIXES = ("/docs", "/redoc")


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.user_claims = None
        header = request.headers.get("authorization") or ""
        if header.lower().startswith("bearer "):
            try:
                request.state.user_claims = decode_access_token(header[7:].strip())
            except TokenError:
                request.state.user_claims = None
        path = request.url.path.rstrip("/") or "/"
        if path in PUBLIC_PATHS or path.startswith(PUBLIC_PREFIXES):
            return await call_next(request)
        if request.method == "OPTIONS":
            return await call_next(request)
        if request.state.user_claims is None:
            return JSONResponse(
                status_code=401,
                content=error_envelope(
                    ErrorCode.UNAUTHORIZED.value,
                    "未登录或登录已过期",
                    getattr(request.state, "request_id", None),
                ),
            )
        return await call_next(request)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    claims = getattr(request.state, "user_claims", None)
    if not claims or not claims.get("sub"):
        raise AppError(ErrorCode.UNAUTHORIZED)
    user = db.get(User, int(claims["sub"]))
    if user is None:
        raise AppError(ErrorCode.UNAUTHORIZED)
    auth_service.reset_daily_quota_if_needed(db, user)
    return user
