import os

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.constants.error_codes import AppError, ErrorCode
from app.log_helpers import audit_event  # noqa: F401  (re-exported for controllers)
from app.models import ColumnProfile, Dataset, Issue, QualityRule, RuleRun, User
from app.profiling.loader import load_frame
from app.schemas.dataset import serialize_dataset
from app.utils import storage
from app.utils.logger import log_event


def _profile_run(db: Session, dataset_id: int):
    return (
        db.query(RuleRun)
        .filter(RuleRun.dataset_id == dataset_id, RuleRun.kind == "profile")
        .order_by(RuleRun.id.desc())
        .first()
    )


def _rule_count(db: Session, dataset_id: int) -> int:
    return db.query(func.count(QualityRule.id)).filter(QualityRule.dataset_id == dataset_id).scalar() or 0


def _open_issue_count(db: Session, dataset_id: int) -> int:
    return (
        db.query(func.count(Issue.id))
        .join(RuleRun, Issue.rule_run_id == RuleRun.id)
        .filter(RuleRun.dataset_id == dataset_id, Issue.status.in_(["open", "triaged"]))
        .scalar()
        or 0
    )


def serialize(db: Session, dataset: Dataset) -> dict:
    return serialize_dataset(
        dataset,
        profile_run=_profile_run(db, dataset.id),
        rule_count=_rule_count(db, dataset.id),
        open_issues=_open_issue_count(db, dataset.id),
    )


def list_datasets(db: Session, include_deleted: bool = False) -> list[Dataset]:
    query = db.query(Dataset)
    if not include_deleted:
        query = query.filter(Dataset.is_deleted.is_(False))
    return query.order_by(Dataset.id.asc()).all()


def get_dataset(db: Session, dataset_id: int) -> Dataset:
    dataset = db.get(Dataset, dataset_id)
    if dataset is None or dataset.is_deleted:
        raise AppError(ErrorCode.DATASET_NOT_FOUND, detail={"dataset_id": dataset_id})
    return dataset


def upsert_dataset(
    db: Session,
    owner: User,
    filename: str,
    payload: bytes,
    source_format: str | None = None,
) -> tuple[Dataset, bool]:
    """Validate + persist one upload. Same (name, owner) re-uses the row (re-upload)."""
    fmt = source_format or storage.detect_format(filename)
    if not fmt:
        raise AppError(
            ErrorCode.FORMAT_UNSUPPORTED,
            message="仅支持 .csv / .parquet / .jsonl / .xlsx",
            detail={"filename": filename},
        )
    size = len(payload)
    if size > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise AppError(
            ErrorCode.ROW_LIMIT_EXCEEDED,
            message=f"文件超过 {settings.MAX_UPLOAD_MB}MB 上限",
            detail={"size_bytes": size},
        )
    log_event("UPLOAD_STARTED", name=filename, size_bytes=size, source_format=fmt)

    path, checksum, safe_name = storage.save_upload(filename, payload)
    try:
        loaded = load_frame(path, fmt)
    except AppError:
        storage.remove_file(path)
        raise
    except Exception as exc:
        storage.remove_file(path)
        raise AppError(
            ErrorCode.FORMAT_UNSUPPORTED,
            message="文件无法解析",
            detail={"filename": filename, "error": str(exc)},
        ) from exc

    dataset = (
        db.query(Dataset)
        .filter(Dataset.name == safe_name, Dataset.owner_id == owner.id)
        .first()
    )
    created = dataset is None
    if dataset is None:
        dataset = Dataset(
            owner_id=owner.id,
            name=safe_name,
            source_format=fmt,
            file_path=path,
            checksum=checksum,
        )
        db.add(dataset)
    else:
        old_path = dataset.file_path
        dataset.source_format = fmt
        dataset.file_path = path
        dataset.checksum = checksum
        dataset.is_deleted = False
        if old_path and old_path != path and os.path.exists(old_path):
            storage.remove_file(old_path)
    dataset.row_count = loaded.row_count
    dataset.column_count = loaded.column_count
    dataset.file_size = size
    dataset.status = "uploaded"
    db.commit()
    db.refresh(dataset)

    log_event(
        "UPLOAD_SUCCEEDED",
        dataset_id=dataset.id,
        rows=loaded.row_count,
        columns=loaded.column_count,
        checksum=checksum[:12],
    )
    return dataset, created


def delete_dataset(db: Session, dataset: Dataset, actor: User) -> dict:
    before = {"id": dataset.id, "name": dataset.name}
    dataset.is_deleted = True
    dataset.status = "deleted"
    db.query(QualityRule).filter(QualityRule.dataset_id == dataset.id).delete()
    db.query(ColumnProfile).filter(ColumnProfile.dataset_id == dataset.id).delete()
    db.commit()
    removed = storage.remove_file(dataset.file_path)
    if not removed:
        log_event("DATASET_FILE_MISSING", dataset_id=dataset.id, path=dataset.file_path)
    log_event("DATASET_DELETED", dataset_id=dataset.id, name=dataset.name)
    return before
