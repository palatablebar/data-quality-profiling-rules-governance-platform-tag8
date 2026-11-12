from sqlalchemy.orm import Session

from app.constants.messages import AUDIT_ACTIONS
from app.log_helpers import audit_event
from app.models import User
from app.schemas.rule import serialize_rule
from app.services import rule_service, run_service


def list_rules(db: Session, dataset_id: int | None, active_only: bool) -> dict:
    rules = rule_service.list_rules(db, dataset_id=dataset_id, active_only=active_only)
    return {"items": [serialize_rule(rule) for rule in rules], "total": len(rules)}


def create_rule(request, db: Session, user: User, payload) -> dict:
    rule = rule_service.create_rule(db, user, payload)
    audit_event(
        request,
        AUDIT_ACTIONS["RULE_CREATE"],
        "QualityRule",
        rule.id,
        None,
        {"name": rule.name, "rule_type": rule.rule_type, "column_name": rule.column_name, "severity": rule.severity},
    )
    return serialize_rule(rule)


def update_rule(request, db: Session, user: User, rule_id: int, payload) -> dict:
    rule = _get_rule(db, rule_id)
    rule, before = rule_service.update_rule(db, user, rule, payload)
    audit_event(
        request,
        AUDIT_ACTIONS["RULE_UPDATE"],
        "QualityRule",
        rule_id,
        before,
        {"name": rule.name, "rule_type": rule.rule_type, "column_name": rule.column_name, "severity": rule.severity},
    )
    return serialize_rule(rule)


def toggle_rule(request, db: Session, user: User, rule_id: int, is_active: bool) -> dict:
    rule = _get_rule(db, rule_id)
    rule, before = rule_service.toggle_rule(db, user, rule, is_active)
    audit_event(request, AUDIT_ACTIONS["RULE_TOGGLE"], "QualityRule", rule_id, {"is_active": before}, {"is_active": rule.is_active})
    return serialize_rule(rule)


def delete_rule(request, db: Session, user: User, rule_id: int) -> dict:
    rule = _get_rule(db, rule_id)
    before = rule_service.delete_rule(db, user, rule)
    audit_event(request, AUDIT_ACTIONS["RULE_DELETE"], "QualityRule", rule_id, before, None)
    return {"deleted": True, "rule_id": rule_id}


def bulk_run(request, db: Session, user: User, payload) -> dict:
    run = run_service.bulk_run(db, user, payload.dataset_id, payload.rule_ids)
    audit_event(
        request,
        AUDIT_ACTIONS["RULE_BULK_RUN"],
        "RuleRun",
        run.id,
        None,
        {"dataset_id": run.dataset_id, "rules_total": run.rules_total},
    )
    return {"run_id": run.id, "status": run.status, "rules_total": run.rules_total}


def _get_rule(db: Session, rule_id: int):
    from app.constants.error_codes import AppError, ErrorCode
    from app.models import QualityRule

    rule = db.get(QualityRule, rule_id)
    if rule is None:
        raise AppError(ErrorCode.RULE_PARAMS_INVALID, message="规则不存在", status_code=404, detail={"rule_id": rule_id})
    return rule
