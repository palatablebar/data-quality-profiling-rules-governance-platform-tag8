from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.controllers import issue_controller
from app.middlewares.auth import get_current_user
from app.middlewares.rbac import require_roles
from app.models import User
from app.schemas.issue import BulkAssignRequest, IssueUpdate

router = APIRouter(prefix="/issues", tags=["issues"])


@router.get("")
def list_issues(
    dataset_id: int | None = None,
    severity: str | None = None,
    status: str | None = None,
    rule_id: int | None = None,
    assignee_id: int | None = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return issue_controller.list_issues(
        db,
        dataset_id=dataset_id,
        severity=severity,
        status=status,
        rule_id=rule_id,
        assignee_id=assignee_id,
        page=page,
        page_size=page_size,
    )


@router.get("/summary")
def summary(dataset_id: int | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return issue_controller.summary(db, dataset_id)


@router.get("/{issue_id}")
def get_issue(issue_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return issue_controller.get_issue(db, issue_id)


@router.patch("/{issue_id}")
def update_issue(
    issue_id: int,
    payload: IssueUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("steward", "analyst")),
):
    return issue_controller.update_issue(request, db, user, issue_id, payload)


@router.post("/bulk-assign")
def bulk_assign(
    payload: BulkAssignRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("steward", "analyst")),
):
    return issue_controller.bulk_assign(request, db, user, payload)
