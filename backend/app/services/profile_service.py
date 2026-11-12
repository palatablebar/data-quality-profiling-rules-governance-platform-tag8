import time
from datetime import datetime

from sqlalchemy.orm import Session

from app.constants.column_type import ColumnType
from app.constants.error_codes import AppError, ErrorCode
from app.constants.rule_run_status import ACTIVE_STATUSES, RuleRunStatus
from app.models import ColumnProfile, Dataset, RuleRun, User
from app.profiling import pattern, stats, type_infer
from app.profiling.loader import load_frame
from app.profiling.suggest import suggest_for_dataset
from app.schemas.dataset import serialize_profile_run_ref
from app.schemas.profile import serialize_column_profile
from app.utils.logger import log_event


def start_profile(db: Session, actor: User, dataset: Dataset) -> RuleRun:
    from app.middlewares.quota import consume_scan

    lock_token = consume_scan(db, actor, dataset.id, "profile")
    run = RuleRun(
        dataset_id=dataset.id,
        kind="profile",
        triggered_by=actor.id,
        status=RuleRunStatus.QUEUED.value,
        lock_token=lock_token,
    )
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
    # claim the batch (queued/failed -> running); a cancel that landed first wins
    claimed = (
        db.query(RuleRun)
        .filter(
            RuleRun.id == run.id,
            RuleRun.status.in_([RuleRunStatus.QUEUED.value, RuleRunStatus.FAILED.value]),
        )
        .update(
            {RuleRun.status: RuleRunStatus.RUNNING.value, RuleRun.started_at: datetime.now()},
            synchronize_session=False,
        )
    )
    db.commit()
    if not claimed:
        db.refresh(run)
        log_event("RUN_CANCEL_OBSERVED", run_id=run.id, finished_rules=0, total=0)
        return 0

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
    duration_ms = int((time.perf_counter() - started) * 1000)
    db.commit()
    # guarded terminal write: a cancelled profile run stays cancelled
    finished = (
        db.query(RuleRun)
        .filter(RuleRun.id == run.id, RuleRun.status.in_(sorted(ACTIVE_STATUSES)))
        .update(
            {
                RuleRun.rules_total: created,
                RuleRun.rules_passed: created,
                RuleRun.rows_scanned: total_rows,
                RuleRun.duration_ms: duration_ms,
                RuleRun.status: RuleRunStatus.SUCCEEDED.value,
                RuleRun.finished_at: datetime.now(),
            },
            synchronize_session=False,
        )
    )
    db.commit()
    if not finished:
        db.refresh(run)
        log_event("RUN_STALE_FINISH", run_id=run.id, status=run.status)
        return created
    log_event(
        "PROFILE_FINISHED",
        dataset_id=dataset.id,
        run_id=run.id,
        columns=created,
        duration_ms=duration_ms,
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
