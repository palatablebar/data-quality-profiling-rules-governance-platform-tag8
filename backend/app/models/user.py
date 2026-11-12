from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(190), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    # role: steward | analyst | viewer  (see app/constants/... ; enum lives in frontend types/user.ts)
    role: Mapped[str] = mapped_column(String(16), nullable=False, default="viewer")
    daily_scan_quota: Mapped[int] = mapped_column(Integer, nullable=False, default=40)
    quota_used_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    quota_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    datasets = relationship("Dataset", back_populates="owner", foreign_keys="Dataset.owner_id")
    assigned_issues = relationship("Issue", back_populates="assignee", foreign_keys="Issue.assignee_id")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User {self.email} role={self.role}>"
