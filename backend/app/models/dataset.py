from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class Dataset(Base):
    __tablename__ = "datasets"
    __table_args__ = (UniqueConstraint("name", "owner_id", name="uq_dataset_name_owner"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    # source_format: csv | parquet | jsonl | xlsx
    source_format: Mapped[str] = mapped_column(String(16), nullable=False, default="csv")
    row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    column_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="uploaded")
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    owner = relationship("User", back_populates="datasets", foreign_keys=[owner_id])
    profiles = relationship("ColumnProfile", back_populates="dataset", cascade="all, delete-orphan")
    rules = relationship("QualityRule", back_populates="dataset", cascade="all, delete-orphan")
    runs = relationship("RuleRun", back_populates="dataset", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Dataset {self.name} rows={self.row_count}>"
