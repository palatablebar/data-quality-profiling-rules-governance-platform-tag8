import time
from datetime import datetime

from sqlalchemy.orm import Session

from app.constants.column_type import ColumnType
from app.constants.error_codes import AppError, ErrorCode
from app.constants.rule_run_status import RuleRunStatus
from app.models import ColumnProfile, Dataset, RuleRun, User
from app.profiling import pattern, stats, type_infer
from app.profiling.loader import load_frame
from app.profiling.suggest import suggest_for_dataset
from app.schemas.dataset import serialize_profile_run_ref
from app.schemas.profile import serialize_column_profile
from app.utils.logger import log_event


def start_profile(db: Session, actor: User, dataset: Dataset) -> RuleRun:
    from app.middlewares.quota import consume_scan

    consume_scan(db, actor, dataset.id, "profile")
    run = RuleRun(dataset_id=dataset.id, kind="profile", triggered_by=actor.id, status=RuleRunStatus.QUEUED.value)
    db.add(run)
    dataset.status = "profiling"
    db.commit()
    db.refresh(run)
    log_event("PROFILE_ENQUEUED", dataset_id=dataset.id, run_id=run.id)
    return run


def latest_profile_run(db: Session, dataset_id: int) -> RuleRun | None:
    return (
        db.query(RuleRun)
        .filter(RuleRun.dataset_id == dataset_id, RuleRun.kind == "profile")
        .order_by(RuleRun.id.desc())
        .first()
    )


def get_profiles(db: Session, dataset_id: int) -> list[ColumnProfile]:
    return (
        db.query(ColumnProfile)
        .filter(ColumnProfile.dataset_id == dataset_id)
        .order_by(ColumnProfile.ordinal.asc())
        .all()
    )


def compute_profiles(db: Session, dataset: Dataset, run: RuleRun) -> int:
    started = time.perf_counter()
    run.status = RuleRunStatus.RUNNING.value
    run.started_at = datetime.now()
    db.commit()

    loaded = load_frame(dataset.file_path, dataset.source_format)
    df = loaded.df
    total_rows = loaded.row_count
    log_event("PROFILE_STARTED", dataset_id=dataset.id, run_id=run.id, rows=total_rows)

    db.query(ColumnProfile).filter(ColumnProfile.dataset_id == dataset.id).delete()
    db.flush()

    created = 0
    for ordinal, column in enumerate(loaded.columns):
        series = df[column]
        inferred = type_infer.infer_type(series)
        column_stats = stats.compute_stats(series, inferred, total_rows)
        summary = None
        if inferred in (ColumnType.STRING.value, ColumnType.UNKNOWN.value, ColumnType.DATE.value, ColumnType.BOOLEAN.value):
            summary = pattern.pattern_summary(series)
        if summary is None and inferred in (ColumnType.INTEGER.value, ColumnType.DECIMAL.value):
            summary = f"数值列 · min={column_stats['min_value']} max={column_stats['max_value']}"
        db.add(
            ColumnProfile(
                dataset_id=dataset.id,
                run_id=run.id,
                column_name=str(column),
                ordinal=ordinal,
                inferred_type=inferred,
                null_rate=round(column_stats["null_rate"], 4),
                distinct_count=column_stats["distinct_count"],
                min_value=column_stats["min_value"],
                max_value=column_stats["max_value"],
                p50=column_stats["p50"],
                p95=column_stats["p95"],
                top_values_json=column_stats["top_values"],
                pattern_summary=summary,
                outlier_count=column_stats["outlier_count"],
            )
        )
        created += 1

    dataset.row_count = total_rows
    dataset.column_count = len(loaded.columns)
    dataset.status = "profiled"
    run.rules_total = created
    run.rules_passed = created
    run.rows_scanned = total_rows
    run.duration_ms = int((time.perf_counter() - started) * 1000)
    run.status = RuleRunStatus.SUCCEEDED.value
    run.finished_at = datetime.now()
    db.commit()
    log_event(
        "PROFILE_FINISHED",
        dataset_id=dataset.id,
        run_id=run.id,
        columns=created,
        duration_ms=run.duration_ms,
    )
    return created


def profile_payload(db: Session, dataset: Dataset) -> dict:
    run = latest_profile_run(db, dataset.id)
    profiles = get_profiles(db, dataset.id)
    if not profiles:
        raise AppError(
            ErrorCode.PROFILE_NOT_READY,
            detail={"dataset_id": dataset.id},
        )
    columns = [serialize_column_profile(profile) for profile in profiles]
    return {
        "dataset": {
            "id": dataset.id,
            "name": dataset.name,
            "source_format": dataset.source_format,
            "row_count": dataset.row_count,
            "column_count": dataset.column_count,
            "checksum": dataset.checksum,
            "status": dataset.status,
            "uploaded_at": dataset.uploaded_at.strftime("%Y-%m-%d %H:%M:%S") if dataset.uploaded_at else None,
        },
        "run": serialize_profile_run_ref(run) if run else None,
        "columns": columns,
        "recommendations": suggest_for_dataset(columns, dataset.row_count),
    }
