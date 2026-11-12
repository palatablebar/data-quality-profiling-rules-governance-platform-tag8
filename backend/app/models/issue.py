from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class Issue(Base):
    __tablename__ = "issues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rule_run_id: Mapped[int] = mapped_column(ForeignKey("rule_runs.id"), nullable=False, index=True)
    rule_id: Mapped[int | None] = mapped_column(ForeignKey("quality_rules.id"), nullable=True, index=True)
    row_index: Mapped[int] = mapped_column(Integer, nullable=False)
    column_name: Mapped[str] = mapped_column(String(190), nullable=False, default="")
    observed_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_expr: Mapped[str | None] = mapped_column(Text, nullable=True)
    # status: IssueStatus (open|triaged|fixed|ignored)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open", index=True)
    assignee_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    run = relationship("RuleRun", back_populates="issues")
    rule = relationship("QualityRule", back_populates="issues")
    assignee = relationship("User", back_populates="assigned_issues", foreign_keys=[assignee_id])
