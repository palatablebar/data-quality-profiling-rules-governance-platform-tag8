from app.schemas.common import iso
from app.utils.formatters import fmt_int


def serialize_dataset(dataset, profile_run=None, rule_count: int = 0, open_issues: int = 0) -> dict:
    return {
        "id": dataset.id,
        "owner_id": dataset.owner_id,
        "name": dataset.name,
        "source_format": dataset.source_format,
        "row_count": dataset.row_count,
        "column_count": dataset.column_count,
        "file_size": dataset.file_size,
        "checksum": dataset.checksum,
        "status": dataset.status,
        "uploaded_at": iso(dataset.uploaded_at),
        "rule_count": rule_count,
        "open_issues": open_issues,
        "row_count_display": fmt_int(dataset.row_count),
        "last_profile": serialize_profile_run_ref(profile_run) if profile_run else None,
    }


def serialize_profile_run_ref(run) -> dict:
    return {
        "run_id": run.id,
        "status": run.status,
        "started_at": iso(run.started_at),
        "finished_at": iso(run.finished_at),
        "duration_ms": run.duration_ms,
        "rows_scanned": run.rows_scanned,
    }
