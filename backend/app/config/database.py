"""Engine / session factory shared by API and Celery worker."""
from sqlalchemy import create_engine, inspect, text
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


# columns added after the initial schema; create_all never alters existing
# tables, so upgraded volumes get them here (mirrors alembic 20261112_0002)
_RUNTIME_COLUMNS = {
    "rule_runs": {
        "rule_ids": "JSON NULL",
        "lock_token": "VARCHAR(64) NULL",
        "rules_unfinished": "INT NOT NULL DEFAULT 0",
    },
    "rule_run_items": {
        "status": "VARCHAR(16) NOT NULL DEFAULT 'finished'",
    },
}


def _ensure_runtime_columns() -> None:
    """Idempotently add post-initial columns to databases created before them."""
    existing = inspect(engine).get_table_names()
    with engine.begin() as conn:
        for table, columns in _RUNTIME_COLUMNS.items():
            if table not in existing:
                continue
            present = {row["name"] for row in inspect(conn).get_columns(table)}
            for column, ddl in columns.items():
                if column not in present:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))


def init_db(max_attempts: int = 30, delay: float = 2.0) -> None:
    """Create all tables, waiting for MySQL to finish its first boot."""
    import time

    import app.models  # noqa: F401

    last_error = None
    for _ in range(max_attempts):
        try:
            Base.metadata.create_all(bind=engine)
            _ensure_runtime_columns()
            return
        except Exception as exc:  # pragma: no cover - infra retry
            last_error = exc
            time.sleep(delay)
    raise RuntimeError(f"database bootstrap failed: {last_error}")
