"""Celery task: re-scan a dataset and flip issues that no longer reproduce.

Used by ``POST /runs/{id}/recheck`` after the source file is re-exported.
"""
from app.config.celery_app import celery_app
from app.config.database import SessionLocal
from app.constants.rule_type import RuleType
from app.models import Dataset, QualityRule, RuleRun
from app.profiling.loader import load_frame
from app.rules import engine
from app.rules.base import RuleContext
from app.rules.registry import get_checker
from app.utils.logger import log_event


@celery_app.task(name="qualiscope.recheck_issues", bind=True, max_retries=0)
def recheck_issues(self, run_id: int) -> dict:
    db = SessionLocal()
    try:
        run = db.get(RuleRun, run_id)
        if run is None:
            return {"ok": False}
        dataset = db.get(Dataset, run.dataset_id)
        loaded = load_frame(dataset.file_path, dataset.source_format)
        rules = (
            db.query(QualityRule)
            .filter(QualityRule.dataset_id == dataset.id, QualityRule.is_active.is_(True))
            .all()
        )
        violations: dict[int, set[int]] = {}
        for rule in rules:
            if rule.column_name not in loaded.columns:
                continue
            ctx = RuleContext(
                df=loaded.df,
                column=rule.column_name,
                params=dict(rule.params_json or {}),
                sample_limit=max(1, int(rule.sample_limit or 200)),
            )
            if rule.rule_type == RuleType.REFERENTIAL.value:
                ctx.target_values = engine.load_target_values(db, ctx.params)
            result = get_checker(rule.rule_type)(ctx)
            violations[rule.id] = result.violated_rows
        fixed = engine.recheck_open_issues(db, dataset.id, run_id, violations)
        return {"ok": True, "fixed": fixed}
    except Exception as exc:  # pragma: no cover
        log_event("AUDIT_ISSUE_RECHECK", run_id=run_id, fixed_count=0, remaining=-1)
        return {"ok": False, "reason": str(exc)}
    finally:
        db.close()
