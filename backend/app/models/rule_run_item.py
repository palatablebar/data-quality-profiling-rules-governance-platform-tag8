from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class RuleRunItem(Base):
    """One rule's result inside a batch — powers the check-mark progress list."""

    __tablename__ = "rule_run_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("rule_runs.id"), nullable=False, index=True)
    rule_id: Mapped[int | None] = mapped_column(ForeignKey("quality_rules.id"), nullable=True)
    rule_name: Mapped[str] = mapped_column(String(190), nullable=False, default="")
    rule_type: Mapped[str] = mapped_column(String(24), nullable=False, default="")
    column_name: Mapped[str] = mapped_column(String(190), nullable=False, default="")
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    # status: RuleRunItemStatus (finished|cancelled); cancelled = the batch was
    # aborted before this rule ran, row kept so the ledger shows what was skipped
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="finished")
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    violation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    persisted_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_code: Mapped[str | None] = mapped_column(String(24), nullable=True)

    run = relationship("RuleRun", back_populates="items")
