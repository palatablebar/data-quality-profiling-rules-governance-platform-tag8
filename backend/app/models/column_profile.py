from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class ColumnProfile(Base):
    __tablename__ = "column_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), nullable=False, index=True)
    # run_id points at the profiling batch in rule_runs (shared id sequence)
    run_id: Mapped[int | None] = mapped_column(ForeignKey("rule_runs.id"), nullable=True, index=True)
    column_name: Mapped[str] = mapped_column(String(190), nullable=False)
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # inferred_type: ColumnType  (integer|decimal|string|date|boolean|unknown)
    inferred_type: Mapped[str] = mapped_column(String(16), nullable=False, default="unknown")
    null_rate: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False, default=Decimal("0"))
    distinct_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    min_value: Mapped[str | None] = mapped_column(String(200), nullable=True)
    max_value: Mapped[str | None] = mapped_column(String(200), nullable=True)
    p50: Mapped[float | None] = mapped_column(Float, nullable=True)
    p95: Mapped[float | None] = mapped_column(Float, nullable=True)
    top_values_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    pattern_summary: Mapped[str | None] = mapped_column(String(400), nullable=True)
    outlier_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    dataset = relationship("Dataset", back_populates="profiles")
