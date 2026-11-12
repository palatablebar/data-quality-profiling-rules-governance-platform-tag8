from sqlalchemy.orm import Session, joinedload

from app.constants.error_codes import AppError, ErrorCode
from app.constants.issue_status import TRANSITIONS, IssueStatus
from app.models import Issue, QualityRule, RuleRun, User
from app.schemas.issue import serialize_issue
from app.utils.logger import log_event
from app.utils.pagination import paginate_query

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _base_query(db: Session):
    return db.query(Issue).options(
        joinedload(Issue.rule),
        joinedload(Issue.assignee),
        joinedload(Issue.run).joinedload(RuleRun.dataset),
    )


def list_issues(
    db: Session,
    dataset_id: int | None = None,
    severity: str | None = None,
    status: str | None = None,
    rule_id: int | None = None,
    assignee_id: int | None = None,
    page: int = 1,
    page_size: int = 50,
) -> dict:
    query = _base_query(db).join(QualityRule, Issue.rule_id == QualityRule.id)
    if dataset_id is not None:
        query = query.join(RuleRun, Issue.rule_run_id == RuleRun.id).filter(RuleRun.dataset_id == dataset_id)
    if severity:
        query = query.filter(QualityRule.severity == severity)
    if status:
        query = query.filter(Issue.status == status)
    if rule_id is not None:
        query = query.filter(Issue.rule_id == rule_id)
    if assignee_id is not None:
        query = query.filter(Issue.assignee_id == assignee_id)
    result = paginate_query(query.order_by(Issue.id.asc()), page, page_size)
    result["items"] = [serialize_issue(issue) for issue in result["items"]]
    return result


def summary(db: Session, dataset_id: int | None = None) -> dict:
    query = db.query(Issue).join(QualityRule, Issue.rule_id == QualityRule.id)
    if dataset_id is not None:
        query = query.join(RuleRun, Issue.rule_run_id == RuleRun.id).filter(RuleRun.dataset_id == dataset_id)
    rows = query.all()
    by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    by_status = {"open": 0, "triaged": 0, "fixed": 0, "ignored": 0}
    for issue in rows:
        if issue.rule:
            by_severity[issue.rule.severity] = by_severity.get(issue.rule.severity, 0) + 1
        by_status[issue.status] = by_status.get(issue.status, 0) + 1
    return {
        "total": len(rows),
        "by_severity": by_severity,
        "by_status": by_status,
        "dataset_id": dataset_id,
    }


def get_issue(db: Session, issue_id: int) -> Issue:
    issue = _base_query(db).filter(Issue.id == issue_id).first()
    if issue is None:
        raise AppError(ErrorCode.ISSUE_CLOSED, message="问题单不存在", status_code=404, detail={"issue_id": issue_id})
    return issue


def update_issue(db: Session, issue: Issue, payload, actor: User) -> tuple[Issue, dict]:
    before = {
        "status": issue.status,
        "assignee_id": issue.assignee_id,
        "note": issue.note,
    }
    if payload.status and payload.status != issue.status:
        allowed = TRANSITIONS.get(issue.status, set())
        if payload.status not in allowed:
            raise AppError(
                ErrorCode.ISSUE_CLOSED,
                message=f"不允许从 {issue.status} 流转到 {payload.status}",
                detail={"from": issue.status, "to": payload.status, "allowed": sorted(allowed)},
            )
        issue.status = payload.status
    if payload.assignee_id is not None:
        assignee = db.get(User, payload.assignee_id)
        if assignee is None:
            raise AppError(ErrorCode.DATASET_NOT_FOUND, message="指派的用户不存在", status_code=404)
        issue.assignee_id = assignee.id
        if issue.status == IssueStatus.OPEN.value:
            issue.status = IssueStatus.TRIAGED.value
        log_event(
            "AUDIT_ISSUE_ASSIGN",
            issue_id=issue.id,
            assignee_id=issue.assignee_id,
            status=issue.status,
        )
    if payload.note is not None:
        issue.note = payload.note
    db.commit()
    db.refresh(issue)
    if before["status"] != issue.status:
        log_event("AUDIT_ISSUE_STATUS", issue_id=issue.id, before=before["status"], after=issue.status)
    return issue, before


def bulk_assign(db: Session, issues: list[Issue], assignee_id: int | None, status: str | None, actor: User) -> list[Issue]:
    assignee = None
    if assignee_id is not None:
        assignee = db.get(User, assignee_id)
        if assignee is None:
            raise AppError(ErrorCode.DATASET_NOT_FOUND, message="指派的用户不存在", status_code=404)
    for issue in issues:
        before = issue.status
        if assignee is not None:
            issue.assignee_id = assignee.id
            if issue.status == IssueStatus.OPEN.value:
                issue.status = IssueStatus.TRIAGED.value
        if status and status != issue.status:
            allowed = TRANSITIONS.get(issue.status, set())
            if status in allowed:
                issue.status = status
        log_event("AUDIT_ISSUE_ASSIGN", issue_id=issue.id, assignee_id=issue.assignee_id, status=issue.status)
        if before != issue.status:
            log_event("AUDIT_ISSUE_STATUS", issue_id=issue.id, before=before, after=issue.status)
    db.commit()
    return issues
