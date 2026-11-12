"""Celery task: compute every column profile for one dataset snapshot."""
from app.config.celery_app import celery_app
from app.config.database import SessionLocal
from app.constants.rule_run_status import ACTIVE_STATUSES, RuleRunStatus
from app.middlewares import quota
from app.models import Dataset, RuleRun
from app.services import profile_service
from app.utils.logger import log_event


@celery_app.task(name="qualiscope.profile_dataset", bind=True, max_retries=0)
def profile_dataset(self, run_id: int) -> dict:
    db = SessionLocal()
    dataset_id = None
    lock_token = None
    try:
        run = db.get(RuleRun, run_id)
        if run is None:
            return {"ok": False, "reason": "run not found"}
        dataset_id = run.dataset_id
        lock_token = run.lock_token
        if run.status == RuleRunStatus.CANCELLED.value:
            # cancelled while queued: never start
            log_event("RUN_CANCEL_OBSERVED", run_id=run_id, finished_rules=0, total=0)
            return {"ok": False, "cancelled": True}
        dataset = db.get(Dataset, dataset_id)
        if dataset is None:
            db.query(RuleRun).filter(
                RuleRun.id == run_id, RuleRun.status.in_(sorted(ACTIVE_STATUSES))
            ).update({RuleRun.status: RuleRunStatus.FAILED.value}, synchronize_session=False)
            db.commit()
            return {"ok": False, "reason": "dataset not found"}
        try:
            columns = profile_service.compute_profiles(db, dataset, run)
        except Exception as exc:  # pragma: no cover - worker-side failure path
            code = getattr(exc, "code", "QUAL-5000")
            # guarded: a cancel that landed first keeps the batch cancelled
            db.query(RuleRun).filter(
                RuleRun.id == run_id, RuleRun.status.in_(sorted(ACTIVE_STATUSES))
            ).update(
                {RuleRun.status: RuleRunStatus.FAILED.value, RuleRun.error_code: code},
                synchronize_session=False,
            )
            db.commit()
            log_event("RUN_FAILED", run_id=run_id, error_code=code, reason=str(exc))
            raise
        return {"ok": True, "columns": columns}
    finally:
        if dataset_id is not None:
            # token-scoped release: a stale worker must not unlock the next batch
            quota.release_dataset_lock(dataset_id, lock_token)
        db.close()
