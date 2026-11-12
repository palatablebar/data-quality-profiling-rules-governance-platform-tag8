"""Scan quota + Redis sliding-window rate limit + per-dataset execution lock.

* daily quota: users.daily_scan_quota / quota_used / quota_used_date
* sliding window: zset ``rl:qualiscope:{user_id}`` (RATE_WINDOW_SECONDS)
* dataset lock: ``SET runlock:{dataset_id} {token} NX EX`` so one dataset never
  runs twice in parallel. The token identifies the holding batch: a stale worker
  finishing late can only release its own lock, never the next batch's.
"""
import time
import uuid
from datetime import date

import redis
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware

from app.config.settings import settings
from app.constants.error_codes import AppError, ErrorCode
from app.models import User
from app.utils.logger import log_event

_client = None
_mem_window: dict[str, list[float]] = {}
_mem_locks: dict[int, tuple[str, float]] = {}
LOCK_TTL_SECONDS = 1800

# compare-and-delete so a late finish signal only releases its own batch's lock
_RELEASE_LOCK_LUA = """
if redis.call('get', KEYS[1]) == ARGV[1] then
  return redis.call('del', KEYS[1])
end
return 0
"""


def get_redis():
    global _client
    if _client is None:
        try:
            _client = redis.Redis.from_url(
                settings.REDIS_URL, socket_timeout=0.4, socket_connect_timeout=0.4, decode_responses=True
            )
            _client.ping()
        except Exception:
            _client = False
    return _client or None


def rate_limit_allow(user_id: int) -> bool:
    window = settings.RATE_WINDOW_SECONDS
    max_hits = settings.RATE_WINDOW_MAX
    now = time.time()
    key = f"rl:qualiscope:{user_id}"
    client = get_redis()
    if client is not None:
        try:
            pipe = client.pipeline()
            pipe.zremrangebyscore(key, 0, now - window)
            pipe.zadd(key, {f"{now:.6f}": now})
            pipe.zcard(key)
            pipe.expire(key, window)
            _, _, count, _ = pipe.execute()
            allowed = int(count) <= max_hits
        except Exception:
            allowed = _mem_allow(key, now, window, max_hits)
    else:
        allowed = _mem_allow(key, now, window, max_hits)
    if not allowed:
        log_event("AUDIT_RATE_LIMITED", user_id=user_id, window_max=max_hits)
    return allowed


def _mem_allow(key: str, now: float, window: int, max_hits: int) -> bool:
    hits = [t for t in _mem_window.get(key, []) if t > now - window]
    hits.append(now)
    _mem_window[key] = hits
    return len(hits) <= max_hits


def new_lock_token() -> str:
    return uuid.uuid4().hex


def acquire_dataset_lock(dataset_id: int, token: str) -> bool:
    client = get_redis()
    if client is not None:
        try:
            return bool(client.set(f"runlock:{dataset_id}", token, nx=True, ex=LOCK_TTL_SECONDS))
        except Exception:
            pass
    held = _mem_locks.get(dataset_id)
    if held and held[1] > time.time():
        return False
    _mem_locks[dataset_id] = (token, time.time() + LOCK_TTL_SECONDS)
    return True


def release_dataset_lock(dataset_id: int, token: str | None = None) -> None:
    """Release the per-dataset lock.

    With ``token`` the lock is only removed when the token still matches the
    holder — a stale worker's late ``finally`` must not unlock the batch that
    started after it. ``token=None`` force-releases (legacy rows without one).
    """
    client = get_redis()
    if client is not None:
        try:
            if token is None:
                client.delete(f"runlock:{dataset_id}")
            else:
                client.eval(_RELEASE_LOCK_LUA, 1, f"runlock:{dataset_id}", token)
        except Exception:
            pass
    held = _mem_locks.get(dataset_id)
    if held and (token is None or held[0] == token):
        _mem_locks.pop(dataset_id, None)


def quota_snapshot(user: User) -> dict:
    quota = int(user.daily_scan_quota or 0)
    used = int(user.quota_used or 0)
    return {
        "daily_scan_quota": quota,
        "quota_used": used,
        "quota_remaining": max(0, quota - used),
        "quota_used_date": user.quota_used_date.strftime("%Y-%m-%d") if user.quota_used_date else None,
        "window_max": settings.RATE_WINDOW_MAX,
        "window_seconds": settings.RATE_WINDOW_SECONDS,
    }


def consume_scan(db: Session, user: User, dataset_id: int, action: str) -> str:
    """Charge quota and take the dataset lock; returns the lock token.

    The caller persists the token on the run row so both the API (cancel path)
    and the worker (late ``finally``) release only the lock this batch holds.
    """
    today = date.today()
    if user.quota_used_date != today:
        user.quota_used_date = today
        user.quota_used = 0
    if not rate_limit_allow(user.id):
        raise AppError(
            ErrorCode.RATE_LIMITED,
            detail={"retry_after": settings.RATE_WINDOW_SECONDS},
        )
    if user.quota_used >= user.daily_scan_quota:
        log_event(
            "AUDIT_QUOTA_REJECTED",
            user_id=user.id,
            used=user.quota_used,
            quota=user.daily_scan_quota,
        )
        raise AppError(
            ErrorCode.QUOTA_EXHAUSTED,
            detail={
                "quota": user.daily_scan_quota,
                "used": user.quota_used,
                "retry_after": 3600,
            },
        )
    token = new_lock_token()
    if not acquire_dataset_lock(dataset_id, token):
        log_event("PROFILE_RUN_LOCKED", dataset_id=dataset_id, user_id=user.id)
        raise AppError(ErrorCode.RUN_LOCKED, detail={"dataset_id": dataset_id, "action": action})
    user.quota_used += 1
    db.commit()
    return token


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Redis sliding window on write requests; 429 carries retry_after."""

    WRITE_METHODS = {"POST", "PATCH", "PUT", "DELETE"}

    async def dispatch(self, request, call_next):
        if request.method in self.WRITE_METHODS:
            claims = getattr(request.state, "user_claims", None) or {}
            user_id = claims.get("sub")
            if user_id and not rate_limit_allow(int(user_id)):
                from starlette.responses import JSONResponse

                from app.schemas.common import error_envelope

                return JSONResponse(
                    status_code=429,
                    content=error_envelope(
                        ErrorCode.RATE_LIMITED.value,
                        "请求过于频繁",
                        getattr(request.state, "request_id", None),
                        {"retry_after": settings.RATE_WINDOW_SECONDS},
                    ),
                )
        return await call_next(request)
