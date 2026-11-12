from sqlalchemy.orm import Session

from app.models import User
from app.services import run_service


def list_runs(db: Session, dataset_id: int | None, kind: str | None, limit: int) -> dict:
    runs = run_service.list_runs(db, dataset_id=dataset_id, kind=kind, limit=limit)
    from app.models import Dataset

    datasets = {dataset.id: dataset for dataset in db.query(Dataset).all()}
    from app.schemas.run import serialize_run

    return {
        "items": [serialize_run(run, datasets.get(run.dataset_id)) for run in runs],
        "total": len(runs),
    }


def get_run(db: Session, run_id: int) -> dict:
    return run_service.run_detail(db, run_service.get_run(db, run_id))


def report(db: Session, run_id: int) -> dict:
    return run_service.build_report(db, run_service.get_run(db, run_id))


def recheck(db: Session, run_id: int) -> dict:
    from app.config.celery_app import celery_app

    run = run_service.get_run(db, run_id)
    celery_app.send_task("qualiscope.recheck_issues", args=[run.id])
    return {"ok": True, "run_id": run.id, "message": "复检任务已入队"}


def cancel(db: Session, user: User, run_id: int) -> dict:
    from app.schemas.run import serialize_run

    run = run_service.cancel_run(db, run_service.get_run(db, run_id), user)
    return serialize_run(run)
