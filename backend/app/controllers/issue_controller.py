from sqlalchemy.orm import Session

from app.constants.messages import AUDIT_ACTIONS
from app.log_helpers import audit_event
from app.models import User
from app.schemas.issue import serialize_issue
from app.services import issue_service


def list_issues(db: Session, **filters) -> dict:
    return issue_service.list_issues(db, **filters)


def summary(db: Session, dataset_id: int | None) -> dict:
    return issue_service.summary(db, dataset_id)


def get_issue(db: Session, issue_id: int) -> dict:
    return serialize_issue(issue_service.get_issue(db, issue_id))


def update_issue(request, db: Session, user: User, issue_id: int, payload) -> dict:
    issue = issue_service.get_issue(db, issue_id)
    issue, before = issue_service.update_issue(db, issue, payload, user)
    action = AUDIT_ACTIONS["ISSUE_ASSIGN"] if payload.assignee_id else AUDIT_ACTIONS["ISSUE_STATUS"]
    audit_event(
        request,
        action,
        "Issue",
        issue_id,
        before,
        {"status": issue.status, "assignee_id": issue.assignee_id},
    )
    return serialize_issue(issue)


def bulk_assign(request, db: Session, user: User, payload) -> dict:
    issues = [issue_service.get_issue(db, issue_id) for issue_id in payload.issue_ids]
    updated = issue_service.bulk_assign(db, issues, payload.assignee_id, payload.status, user)
    audit_event(
        request,
        AUDIT_ACTIONS["ISSUE_ASSIGN"],
        "Issue",
        None,
        None,
        {"issue_ids": payload.issue_ids, "assignee_id": payload.assignee_id, "status": payload.status},
    )
    return {"updated": len(updated), "issue_ids": [issue.id for issue in updated]}
