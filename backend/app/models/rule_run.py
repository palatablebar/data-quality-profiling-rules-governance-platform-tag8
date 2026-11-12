from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class RuleRun(Base):
    """Both profiling batches and rule-execution batches live here (kind column),
    so ``column_profiles.run_id`` and ``rule_runs.id`` share one id sequence."""

    __tablename__ = "rule_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), nullable=False, index=True)
    # kind: profile | rules
    kind: Mapped[str] = mapped_column(String(16), nullable=False, default="rules", index=True)
    triggered_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    # status: RuleRunStatus (queued|running|succeeded|failed|cancelled)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="queued", index=True)
    rules_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rules_passed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rules_failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # rules that never finished because the batch was cancelled mid-flight
    rules_unfinished: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rows_scanned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    report_no: Mapped[str | None] = mapped_column(String(40), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(24), nullable=True)
    # snapshot of the rule ids dispatched with this batch (drives cancel bookkeeping)
    rule_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # token proving this run holds the per-dataset execution lock; a stale worker
    # finishing late must not release the lock a newer batch already acquired
    lock_token: Mapped[str | None] = mapped_column(String(64), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    dataset = relationship("Dataset", back_populates="runs")
    items = relationship("RuleRunItem", back_populates="run", cascade="all, delete-orphan")
    issues = relationship("Issue", back_populates="run", cascade="all, delete-orphan")
