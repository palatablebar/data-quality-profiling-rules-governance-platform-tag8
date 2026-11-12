from app.schemas.common import iso
from app.utils.formatters import fmt_duration, fmt_int


def serialize_run_item(item) -> dict:
    return {
        "id": item.id,
        "rule_id": item.rule_id,
        "rule_name": item.rule_name,
        "rule_type": item.rule_type,
        "column_name": item.column_name,
        "severity": item.severity,
        "passed": item.passed,
        "violation_count": item.violation_count,
        "persisted_count": item.persisted_count,
        "duration_ms": item.duration_ms,
        "duration_display": fmt_duration(item.duration_ms),
        "error_code": item.error_code,
    }


def serialize_run(run, dataset=None, with_items: bool = False) -> dict:
    payload = {
        "id": run.id,
        "dataset_id": run.dataset_id,
        "dataset_name": dataset.name if dataset else None,
        "dataset_format": dataset.source_format if dataset else None,
        "kind": run.kind,
        "triggered_by": run.triggered_by,
        "status": run.status,
        "rules_total": run.rules_total,
        "rules_passed": run.rules_passed,
        "rules_failed": run.rules_failed,
        "rows_scanned": run.rows_scanned,
        "rows_scanned_display": fmt_int(run.rows_scanned),
        "duration_ms": run.duration_ms,
        "duration_display": fmt_duration(run.duration_ms),
        "report_no": run.report_no,
        "error_code": run.error_code,
        "started_at": iso(run.started_at),
        "finished_at": iso(run.finished_at),
        "created_at": iso(run.created_at),
    }
    if with_items:
        payload["items"] = [serialize_run_item(item) for item in run.items]
    return payload
