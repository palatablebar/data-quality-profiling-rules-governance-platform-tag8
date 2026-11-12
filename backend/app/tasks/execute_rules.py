"""Celery task: run one batch of quality rules and materialise Issues."""
from app.config.celery_app import celery_app
from app.config.database import SessionLocal
from app.constants.rule_run_status import RuleRunStatus
from app.middlewares import quota
from app.models import Dataset, QualityRule, RuleRun
from app.rules import engine
from app.utils.logger import log_event
from app.constants.messages import TASK_FAILURE_MESSAGES


@celery_app.task(name="qualiscope.execute_rules", bind=True, max_retries=0)
def execute_rules(self, run_id: int, rule_ids: list[int]) -> dict:
    db = SessionLocal()
    dataset_id = None
    try:
        run = db.get(RuleRun, run_id)
        if run is None:
            return {"ok": False, "reason": "run not found"}
        dataset_id = run.dataset_id
        dataset = db.get(Dataset, dataset_id)
        rules = (
            db.query(QualityRule)
            .filter(QualityRule.id.in_(rule_ids or []))
            .order_by(QualityRule.id.asc())
            .all()
        )
        try:
            summary = engine.execute_batch(db, run, dataset, rules, triggered_by=run.triggered_by)
            engine.recheck_open_issues(db, dataset_id, run.id, summary["violations_by_rule"])
        except Exception as exc:  # pragma: no cover - worker-side failure path
            code = getattr(exc, "code", "QUAL-5000")
            run.status = RuleRunStatus.FAILED.value
            run.error_code = code
            db.commit()
            log_event(
                "RUN_FAILED",
                run_id=run_id,
                error_code=code,
                reason=TASK_FAILURE_MESSAGES["RUN_FAILED"].format(reason=str(exc)),
            )
            raise
        return {"ok": True, **{k: v for k, v in summary.items() if k != "violations_by_rule"}}
    finally:
        if dataset_id is not None:
            quota.release_dataset_lock(dataset_id)
        db.close()
