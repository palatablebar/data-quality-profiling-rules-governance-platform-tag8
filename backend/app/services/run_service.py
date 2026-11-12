import time

from sqlalchemy.orm import Session

from app.config.celery_app import celery_app
from app.constants.error_codes import AppError, ErrorCode
from app.constants.rule_run_status import RuleRunStatus
from app.models import ColumnProfile, Dataset, Issue, QualityRule, RuleRun, RuleRunItem, User
from app.middlewares import quota
from app.schemas.profile import serialize_column_profile
from app.schemas.run import serialize_run, serialize_run_item
from app.utils.logger import log_event


def dispatch_execute_run(run_id: int, rule_ids: list[int]) -> None:
    """Send to Celery; if the broker is unreachable run inline so the API still works."""
    if quota.get_redis() is not None:
        try:
            celery_app.send_task("qualiscope.execute_rules", args=[run_id, rule_ids])
            return
        except Exception as exc:  # pragma: no cover - broker outage
            log_event("RUN_FAILED", run_id=run_id, error_code="QUAL-5000", reason=f"broker: {exc}")
    from app.tasks.execute_rules import execute_rules

    execute_rules(run_id, rule_ids)


def dispatch_profile_run(run_id: int) -> None:
    if quota.get_redis() is not None:
        try:
            celery_app.send_task("qualiscope.profile_dataset", args=[run_id])
            return
        except Exception as exc:  # pragma: no cover
            log_event("PROFILE_TIMEOUT", dataset_id="-", run_id=run_id, duration_ms=0)
    from app.tasks.profile_dataset import profile_dataset

    profile_dataset(run_id)


def bulk_run(db: Session, actor: User, dataset_id: int, rule_ids: list[int] | None = None) -> RuleRun:
    dataset = db.get(Dataset, dataset_id)
    if dataset is None or dataset.is_deleted:
        raise AppError(ErrorCode.DATASET_NOT_FOUND, detail={"dataset_id": dataset_id})
    query = db.query(QualityRule).filter(QualityRule.dataset_id == dataset_id, QualityRule.is_active.is_(True))
    if rule_ids:
        query = query.filter(QualityRule.id.in_(rule_ids))
    rules = query.order_by(QualityRule.id.asc()).all()
    if not rules:
        raise AppError(
            ErrorCode.RULE_PARAMS_INVALID,
            message="没有可执行的启用规则",
            detail={"dataset_id": dataset_id},
        )
    quota.consume_scan(db, actor, dataset_id, "run")
    run = RuleRun(
        dataset_id=dataset_id,
        kind="rules",
        triggered_by=actor.id,
        status=RuleRunStatus.QUEUED.value,
        rules_total=len(rules),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    log_event("AUDIT_RULE_BULK_RUN", run_id=run.id, dataset_id=dataset_id, rules_total=len(rules))
    dispatch_execute_run(run.id, [rule.id for rule in rules])
    return run


def list_runs(db: Session, dataset_id: int | None = None, kind: str | None = "rules", limit: int = 50) -> list[RuleRun]:
    query = db.query(RuleRun)
    if dataset_id is not None:
        query = query.filter(RuleRun.dataset_id == dataset_id)
    if kind:
        query = query.filter(RuleRun.kind == kind)
    return query.order_by(RuleRun.id.desc()).limit(limit).all()


def get_run(db: Session, run_id: int) -> RuleRun:
    run = db.get(RuleRun, run_id)
    if run is None:
        raise AppError(ErrorCode.DATASET_NOT_FOUND, message="批次不存在", detail={"run_id": run_id}, status_code=404)
    return run


def run_detail(db: Session, run: RuleRun) -> dict:
    dataset = db.get(Dataset, run.dataset_id)
    payload = serialize_run(run, dataset, with_items=True)
    issue_count = db.query(Issue).filter(Issue.rule_run_id == run.id).count()
    payload["issue_count"] = issue_count
    return payload


def cancel_run(db: Session, run: RuleRun, actor: User) -> RuleRun:
    if run.status not in (RuleRunStatus.QUEUED.value, RuleRunStatus.RUNNING.value):
        raise AppError(ErrorCode.RUN_LOCKED, message="批次已结束，无法取消", detail={"run_id": run.id})
    run.status = RuleRunStatus.FAILED.value
    run.error_code = "QUAL-5010"
    run.finished_at = run.finished_at or run.started_at
    db.commit()
    db.refresh(run)
    quota.release_dataset_lock(run.dataset_id)
    log_event("RUN_CANCELLED", run_id=run.id, actor_id=actor.id)
    return run


def build_report(db: Session, run: RuleRun) -> dict:
    dataset = db.get(Dataset, run.dataset_id)
    items = db.query(RuleRunItem).filter(RuleRunItem.run_id == run.id).all()
    rule_ids = [item.rule_id for item in items if item.rule_id]
    rules = {
        rule.id: rule
        for rule in db.query(QualityRule).filter(QualityRule.id.in_(rule_ids)).all()
    } if rule_ids else {}
    issues = (
        db.query(Issue)
        .filter(Issue.rule_run_id == run.id)
        .order_by(Issue.id.asc())
        .limit(200)
        .all()
    )
    profiles = (
        db.query(ColumnProfile)
        .filter(ColumnProfile.dataset_id == run.dataset_id)
        .order_by(ColumnProfile.ordinal.asc())
        .all()
    )
    from app.utils.formatters import fmt_percentile, rule_param_summary

    return {
        "report_no": run.report_no or f"QC-202611-{run.id:03d}",
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "dataset": {
            "id": dataset.id,
            "name": dataset.name,
            "source_format": dataset.source_format,
            "row_count": dataset.row_count,
            "column_count": dataset.column_count,
            "checksum": dataset.checksum,
        },
        "batch": serialize_run(run, dataset),
        "rules": [
            {
                **serialize_run_item(item),
                "params": (rules.get(item.rule_id).params_json if rules.get(item.rule_id) else {}) or {},
                "param_summary": rule_param_summary(
                    item.rule_type,
                    (rules.get(item.rule_id).params_json if rules.get(item.rule_id) else {}) or {},
                ),
            }
            for item in items
        ],
        "quantiles": [
            {
                "column_name": profile.column_name,
                "inferred_type": profile.inferred_type,
                "null_rate": float(profile.null_rate or 0),
                "min_value": profile.min_value,
                "max_value": profile.max_value,
                "p50": fmt_percentile(profile.p50),
                "p95": fmt_percentile(profile.p95),
                "outlier_count": profile.outlier_count,
            }
            for profile in profiles
        ],
        "violation_samples": [
            {
                "issue_id": issue.id,
                "rule_id": issue.rule_id,
                "rule_name": rules.get(issue.rule_id).name if rules.get(issue.rule_id) else None,
                "severity": rules.get(issue.rule_id).severity if rules.get(issue.rule_id) else None,
                "row_index": issue.row_index,
                "column_name": issue.column_name,
                "observed_value": issue.observed_value,
                "expected_expr": issue.expected_expr,
                "status": issue.status,
            }
            for issue in issues
        ],
        "summary": {
            "rules_total": run.rules_total,
            "rules_passed": run.rules_passed,
            "rules_failed": run.rules_failed,
            "issue_count": len(issues),
            "rows_scanned": run.rows_scanned,
        },
    }


def recent_items(db: Session, dataset_id: int, limit: int = 5) -> list[dict]:
    run = (
        db.query(RuleRun)
        .filter(RuleRun.dataset_id == dataset_id, RuleRun.kind == "rules")
        .order_by(RuleRun.id.desc())
        .first()
    )
    if run is None:
        return []
    items = db.query(RuleRunItem).filter(RuleRunItem.run_id == run.id).limit(limit).all()
    return [serialize_run_item(item) for item in items]
