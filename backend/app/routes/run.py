from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.controllers import rule_controller, run_controller
from app.middlewares.auth import get_current_user
from app.middlewares.rbac import require_roles
from app.models import User
from app.schemas.rule import BulkRunRequest

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("")
def list_runs(
    dataset_id: int | None = None,
    kind: str | None = "rules",
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return run_controller.list_runs(db, dataset_id, kind, limit)


@router.post("")
def bulk_run(
    payload: BulkRunRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("steward", "analyst")),
):
    return rule_controller.bulk_run(request, db, user, payload)


@router.get("/{run_id}")
def get_run(run_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return run_controller.get_run(db, run_id)


@router.get("/{run_id}/report")
def get_report(run_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return run_controller.report(db, run_id)


@router.post("/{run_id}/recheck")
def recheck(run_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("steward", "analyst"))):
    return run_controller.recheck(db, run_id)


@router.post("/{run_id}/cancel")
def cancel(run_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("steward", "analyst"))):
    return run_controller.cancel(db, user, run_id)
