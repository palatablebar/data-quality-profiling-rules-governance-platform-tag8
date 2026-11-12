import time

from fastapi import APIRouter
from sqlalchemy import text

from app.config.database import SessionLocal
from app.middlewares.quota import get_redis

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    database = "ok"
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        database = f"error: {type(exc).__name__}"
    finally:
        db.close()
    redis_state = "ok" if get_redis() is not None else "degraded"
    return {
        "status": "ok",
        "service": "qualiscope-backend",
        "database": database,
        "redis": redis_state,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
