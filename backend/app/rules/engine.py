"""Batch executor: runs every active rule over one dataset snapshot.

Real scanning only — pandas locates the violating rows, then each violating row
is persisted as an Issue with its ``row_index`` (0-based data row, header
excluded) and the original cell text. At most ``sample_limit`` issues per rule
are stored, but ``violation_count`` / ``rules_passed`` / ``rules_failed`` always
reflect the true numbers, and isolated rows are written to the quarantine volume.

Cancellation is cooperative: the loop checks the run row before and after every
rule, commits each finished rule immediately (the partial results stay as
diagnostics), and the terminal write is a guarded UPDATE — once a batch is
cancelled, a late finish signal can never flip its status or results back.
"""
import time
from datetime import datetime

import pandas as pd
from sqlalchemy.orm import Session

from app.constants.error_codes import AppError
from app.constants.issue_status import IssueStatus
from app.constants.rule_run_status import ACTIVE_STATUSES, RuleRunStatus
from app.constants.rule_type import RuleType
from app.constants.severity import Severity
from app.models import Dataset, Issue, QualityRule, RuleRun, RuleRunItem
from app.profiling.loader import load_frame
from app.rules.base import RuleContext, RuleResult
from app.rules.registry import get_checker
from app.utils import storage
from app.utils.formatters import rule_param_summary
from app.utils.logger import log_event

QUARANTINE_ROW_LIMIT = 300


def load_target_values(db: Session, params: dict) -> set[str]:
    target_id = params.get("target_dataset_id")
    column = params.get("target_column")
    target = db.get(Dataset, int(target_id)) if target_id else None
    if target is None or target.is_deleted:
        raise AppError(
            f"QUAL-2010",
            message=f"引用规则的目标数据集缺失（dataset_id={target_id}）",
            detail={"target_dataset_id": target_id},
        )
    loaded = load_frame(target.file_path, target.source_format)
    if column not in loaded.columns:
        raise AppError(
            "QUAL-2010",
            message=f"目标数据集缺少列 {column}",
            detail={"target_column": column, "columns": loaded.columns[:20]},
        )
    series = loaded.df[column].astype(str)
    return {str(value) for value in series if str(value).strip() != ""}


def _report_no_for(run_id: int) -> str:
    """Report numbers derive from the run id: unique even when two batches
    finish concurrently, and stable across re-exports."""
    return f"QC-202611-{run_id:03d}"


def _cancelled_summary(run_id: int, total: int, passed: int = 0, failed: int = 0, rows: int = 0, started: float | None = None) -> dict:
    log_event("RUN_CANCEL_OBSERVED", run_id=run_id, finished_rules=passed + failed, total=total)
    return {
        "cancelled": True,
        "violations_by_rule": {},
        "rules_passed": passed,
        "rules_failed": failed,
        "rows_scanned": rows,
        "duration_ms": int((time.perf_counter() - started) * 1000) if started else 0,
    }


def execute_batch(
    db: Session,
    run: RuleRun,
    dataset: Dataset,
    rules: list[QualityRule],
    triggered_by: int | None = None,
) -> dict:
    started_wall = datetime.now()
    started = time.perf_counter()

    # claim the batch (queued/failed -> running); if a cancel landed first, stop here
    claimed = (
        db.query(RuleRun)
        .filter(
            RuleRun.id == run.id,
            RuleRun.status.in_([RuleRunStatus.QUEUED.value, RuleRunStatus.FAILED.value]),
        )
        .update(
            {
                RuleRun.status: RuleRunStatus.RUNNING.value,
                RuleRun.started_at: started_wall,
                RuleRun.rules_total: len(rules),
            },
            synchronize_session=False,
        )
    )
    db.commit()
    if not claimed:
        return _cancelled_summary(run.id, len(rules), started=started)
    db.refresh(run)

    loaded = load_frame(dataset.file_path, dataset.source_format)
    df = loaded.df
    # the scan size is recorded only while the batch is still live
    db.query(RuleRun).filter(
        RuleRun.id == run.id, RuleRun.status == RuleRunStatus.RUNNING.value
    ).update({RuleRun.rows_scanned: loaded.row_count}, synchronize_session=False)
    db.commit()
    db.refresh(run)
    if run.status == RuleRunStatus.CANCELLED.value:
        return _cancelled_summary(run.id, len(rules), rows=loaded.row_count, started=started)

    log_event(
        "RUN_STARTED",
        run_id=run.id,
        dataset_id=dataset.id,
        rules_total=len(rules),
        rows_scanned=loaded.row_count,
    )

    passed = 0
    failed = 0
    cancelled_observed = False
    violations_by_rule: dict[int, set[int]] = {}
    quarantine_indexes: set[int] = set()

    for rule in rules:
        db.refresh(run)
        if run.status == RuleRunStatus.CANCELLED.value:
            cancelled_observed = True
            break
        rule_started = time.perf_counter()
        item = RuleRunItem(
            run_id=run.id,
            rule_id=rule.id,
            rule_name=rule.name,
            rule_type=rule.rule_type,
            column_name=rule.column_name,
            severity=rule.severity,
            passed=True,
            violation_count=0,
            persisted_count=0,
            duration_ms=0,
        )
        result = RuleResult(violation_count=0, samples=[], expected="")
        error_code = None
        if rule.column_name not in df.columns:
            error_code = "QUAL-2008"
            item.passed = False
            item.error_code = error_code
        else:
            try:
                checker = get_checker(rule.rule_type)
                ctx = RuleContext(
                    df=df,
                    column=rule.column_name,
                    params=dict(rule.params_json or {}),
                    sample_limit=max(1, int(rule.sample_limit or 200)),
                )
                if rule.rule_type == RuleType.REFERENTIAL.value:
                    ctx.target_values = load_target_values(db, ctx.params)
                result = checker(ctx)
            except AppError as exc:
                error_code = exc.code
                item.passed = False
                item.error_code = error_code
                log_event(
                    "RUN_FAILED",
                    run_id=run.id,
                    error_code=exc.code,
                    reason=f"rule#{rule.id} {exc.message}",
                )
            except Exception as exc:  # pragma: no cover - defensive
                error_code = "QUAL-2007"
                item.passed = False
                item.error_code = error_code
                log_event("RUN_FAILED", run_id=run.id, error_code=error_code, reason=str(exc))

        # the cancel may have landed while this rule was scanning. Claim the row
        # with a write-lock probe (self-assigning UPDATE): it serialises against
        # the cancel path's guarded UPDATE, so a lost probe means the batch now
        # belongs to the cancel path and this rule's writes are dropped — the
        # ledger never ends up with both a result and a cancelled placeholder.
        still_live = (
            db.query(RuleRun)
            .filter(RuleRun.id == run.id, RuleRun.status == RuleRunStatus.RUNNING.value)
            .update({RuleRun.status: RuleRunStatus.RUNNING.value}, synchronize_session=False)
        )
        if not still_live:
            cancelled_observed = True
            break

        persisted = 0
        if error_code is None:
            for row_index, observed, expected in result.samples:
                db.add(
                    Issue(
                        rule_run_id=run.id,
                        rule_id=rule.id,
                        row_index=row_index,
                        column_name=rule.column_name,
                        observed_value=observed[:2000],
                        expected_expr=expected[:2000],
                        status=IssueStatus.OPEN.value,
                    )
                )
                persisted += 1
            quarantine_indexes.update(
                row_index for row_index, _, _ in result.samples[:QUARANTINE_ROW_LIMIT]
            )
            violations_by_rule[rule.id] = result.violated_rows
            item.passed = result.violation_count == 0
            item.violation_count = result.violation_count
            log_event(
                "AUDIT_ISSUE_GENERATED",
                run_id=run.id,
                rule_id=rule.id,
                violations=result.violation_count,
                persisted=persisted,
            )
        item.persisted_count = persisted
        item.duration_ms = int((time.perf_counter() - rule_started) * 1000)
        db.add(item)
        if item.passed:
            passed += 1
        else:
            failed += 1
        db.commit()  # each finished rule lands immediately: diagnostics + live progress
        log_event(
            "RUN_RULE_FINISHED",
            run_id=run.id,
            rule_id=rule.id,
            column=rule.column_name,
            passed=item.passed,
            violations=item.violation_count,
            duration_ms=item.duration_ms,
        )

    if quarantine_indexes:
        ordered = sorted(quarantine_indexes)[:QUARANTINE_ROW_LIMIT]
        header = [str(c) for c in df.columns]
        rows = [[str(value) for value in df.loc[idx].tolist()] for idx in ordered if idx in df.index]
        storage.write_quarantine(run.id, header, rows)

    duration_ms = int((time.perf_counter() - started) * 1000)
    if cancelled_observed:
        return _cancelled_summary(run.id, len(rules), passed, failed, loaded.row_count, started)

    # guarded terminal write: a cancel that raced the last rule wins, and this
    # late finish signal is dropped instead of flipping the batch back
    final_values = {
        RuleRun.rules_passed: passed,
        RuleRun.rules_failed: failed,
        RuleRun.rules_unfinished: 0,
        RuleRun.duration_ms: duration_ms,
        RuleRun.status: RuleRunStatus.SUCCEEDED.value,
        RuleRun.finished_at: datetime.now(),
    }
    if run.kind == "rules" and not run.report_no:
        final_values[RuleRun.report_no] = _report_no_for(run.id)
    finished = (
        db.query(RuleRun)
        .filter(RuleRun.id == run.id, RuleRun.status.in_(sorted(ACTIVE_STATUSES)))
        .update(final_values, synchronize_session=False)
    )
    db.commit()
    if not finished:
        db.refresh(run)
        log_event("RUN_STALE_FINISH", run_id=run.id, status=run.status)
        return _cancelled_summary(run.id, len(rules), passed, failed, loaded.row_count, started)

    log_event(
        "RUN_FINISHED",
        run_id=run.id,
        status=RuleRunStatus.SUCCEEDED.value,
        rules_passed=passed,
        rules_failed=failed,
        duration_ms=duration_ms,
    )
    return {
        "cancelled": False,
        "violations_by_rule": violations_by_rule,
        "rules_passed": passed,
        "rules_failed": failed,
        "rows_scanned": loaded.row_count,
        "duration_ms": duration_ms,
    }


def recheck_open_issues(
    db: Session,
    dataset_id: int,
    current_run_id: int,
    violations_by_rule: dict[int, set[int]],
) -> int:
    """After a re-run: previously open issue rows that no longer violate turn `fixed`."""
    fixed = 0
    open_issues = (
        db.query(Issue)
        .filter(
            Issue.status.in_([IssueStatus.OPEN.value, IssueStatus.TRIAGED.value]),
            Issue.rule_run_id != current_run_id,
        )
        .join(QualityRule, Issue.rule_id == QualityRule.id)
        .filter(QualityRule.dataset_id == dataset_id)
        .all()
    )
    for issue in open_issues:
        if issue.rule_id is None:
            continue
        violated = violations_by_rule.get(issue.rule_id)
        if violated is None:
            continue
        if issue.row_index not in violated:
            issue.status = IssueStatus.FIXED.value
            issue.note = (issue.note or "") + f"[recheck run#{current_run_id} 已收敛]"
            fixed += 1
    if fixed:
        db.commit()
    log_event(
        "AUDIT_ISSUE_RECHECK",
        run_id=current_run_id,
        fixed_count=fixed,
        remaining=len(open_issues) - fixed,
    )
    return fixed


def severity_weight_avg(items: list[RuleRunItem]) -> float:
    """Weighted pass rate used by the report export (weight from constants/severity.py)."""
    total = 0.0
    weight = 0.0
    for item in items:
        w = {Severity.LOW.value: 1, Severity.MEDIUM.value: 2, Severity.HIGH.value: 3, Severity.CRITICAL.value: 4}.get(
            item.severity, 1
        )
        total += w
        weight += w if item.passed else 0
    return round(weight / total, 4) if total else 0.0


def summarize_rule(rule: QualityRule) -> str:
    return rule_param_summary(rule.rule_type, rule.params_json or {})
