import time
from datetime import datetime

from sqlalchemy.orm import Session

from app.config.celery_app import celery_app
from app.constants.error_codes import AppError, ErrorCode
from app.constants.issue_status import IssueStatus
from app.constants.rule_run_status import ACTIVE_STATUSES, RuleRunItemStatus, RuleRunStatus
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
    quota_token = quota.consume_scan(db, actor, dataset_id, "run")
    run = RuleRun(
        dataset_id=dataset_id,
        kind="rules",
        triggered_by=actor.id,
        status=RuleRunStatus.QUEUED.value,
        rules_total=len(rules),
        rule_ids=[rule.id for rule in rules],
        lock_token=quota_token,
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
    """Abort a queued/running batch.

    Once this returns, the batch is frozen: its status and business results
    never change again. Issues it already produced are shelved to ``ignored``
    (kept for diagnostics, out of the pending ledger), and rules that never
    ran get a ``cancelled`` placeholder item so the ledger shows the gap.
    """
    # guard update: only a live batch may be cancelled, exactly once
    claimed = (
        db.query(RuleRun)
        .filter(RuleRun.id == run.id, RuleRun.status.in_(sorted(ACTIVE_STATUSES)))
        .update(
            {
                RuleRun.status: RuleRunStatus.CANCELLED.value,
                RuleRun.error_code: "QUAL-5010",
                RuleRun.finished_at: datetime.now(),
            },
            synchronize_session=False,
        )
    )
    if not claimed:
        raise AppError(ErrorCode.RUN_LOCKED, message="批次已结束，无法取消", detail={"run_id": run.id})
    db.commit()  # status lands first: the worker sees it on its next check

    # shelve the partial results: pending issues leave the ledger but stay
    # queryable for diagnostics (ignored is reopenable, so nothing is lost)
    shelved = 0
    pending_issues = (
        db.query(Issue)
        .filter(
            Issue.rule_run_id == run.id,
            Issue.status.in_([IssueStatus.OPEN.value, IssueStatus.TRIAGED.value]),
        )
        .all()
    )
    for issue in pending_issues:
        issue.status = IssueStatus.IGNORED.value
        issue.note = (issue.note or "") + f"[run#{run.id} 批次已中止，仅作诊断留存]"
        shelved += 1

    # mark the rules that never finished so the ledger can name them
    unfinished = 0
    snapshot_ids = list(run.rule_ids or [])
    if run.kind == "rules" and snapshot_ids:
        done_rule_ids = {
            row[0]
            for row in db.query(RuleRunItem.rule_id)
            .filter(RuleRunItem.run_id == run.id, RuleRunItem.rule_id.isnot(None))
            .all()
        }
        missing_ids = [rule_id for rule_id in snapshot_ids if rule_id not in done_rule_ids]
        skipped_rules = (
            db.query(QualityRule).filter(QualityRule.id.in_(missing_ids)).all() if missing_ids else []
        )
        for rule in skipped_rules:
            db.add(
                RuleRunItem(
                    run_id=run.id,
                    rule_id=rule.id,
                    rule_name=rule.name,
                    rule_type=rule.rule_type,
                    column_name=rule.column_name,
                    severity=rule.severity,
                    status=RuleRunItemStatus.CANCELLED.value,
                    passed=False,
                )
            )
            unfinished += 1
    elif run.kind == "rules":
        finished_items = db.query(RuleRunItem).filter(RuleRunItem.run_id == run.id).count()
        unfinished = max(0, (run.rules_total or 0) - finished_items)
    # freeze the partial tallies too: passed/failed reflect the rules that did
    # finish, ``rules_unfinished`` names the gap left by the abort
    finished_rows = (
        db.query(RuleRunItem)
        .filter(RuleRunItem.run_id == run.id, RuleRunItem.status == RuleRunItemStatus.FINISHED.value)
        .all()
    )
    db.query(RuleRun).filter(RuleRun.id == run.id).update(
        {
            RuleRun.rules_unfinished: unfinished,
            RuleRun.rules_passed: sum(1 for item in finished_rows if item.passed),
            RuleRun.rules_failed: sum(1 for item in finished_rows if not item.passed),
        },
        synchronize_session=False,
    )
    db.commit()

    quota.release_dataset_lock(run.dataset_id, run.lock_token)
    db.refresh(run)
    log_event("RUN_CANCELLED", run_id=run.id, actor_id=actor.id)
    log_event("RUN_CANCEL_SHELVED", run_id=run.id, issues=shelved, unfinished=unfinished)
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
