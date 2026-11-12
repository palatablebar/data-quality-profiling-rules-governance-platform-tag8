"""Engine / session factory shared by API and Celery worker."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config.settings import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_size=8,
    max_overflow=4,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(max_attempts: int = 30, delay: float = 2.0) -> None:
    """Create all tables, waiting for MySQL to finish its first boot."""
    import time

    import app.models  # noqa: F401

    last_error = None
    for _ in range(max_attempts):
        try:
            Base.metadata.create_all(bind=engine)
            return
        except Exception as exc:  # pragma: no cover - infra retry
            last_error = exc
            time.sleep(delay)
    raise RuntimeError(f"database bootstrap failed: {last_error}")
