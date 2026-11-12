from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class QualityRule(Base):
    __tablename__ = "quality_rules"
    __table_args__ = (UniqueConstraint("dataset_id", "name", name="uq_rule_name_dataset"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(190), nullable=False)
    # rule_type: RuleType (not_null|unique|range|regex|enum_set|referential|expression)
    rule_type: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    column_name: Mapped[str] = mapped_column(String(190), nullable=False)
    params_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # severity: Severity (low|medium|high|critical)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sample_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=200)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    dataset = relationship("Dataset", back_populates="rules")
    issues = relationship("Issue", back_populates="rule")
