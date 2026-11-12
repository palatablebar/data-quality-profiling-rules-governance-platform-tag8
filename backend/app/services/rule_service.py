from sqlalchemy.orm import Session

from app.constants.column_type import NUMERIC_TYPES, ColumnType
from app.constants.error_codes import AppError, ErrorCode
from app.constants.rule_type import RuleType
from app.models import ColumnProfile, Dataset, QualityRule, User
from app.profiling.suggest import suggest_for_dataset
from app.rules.registry import validate_params
from app.utils.logger import log_event

RULE_TYPE_COLUMN_TYPES = {
    RuleType.RANGE.value: NUMERIC_TYPES,
    RuleType.REGEX.value: {ColumnType.STRING.value, ColumnType.UNKNOWN.value},
    RuleType.ENUM_SET.value: {ColumnType.STRING.value, ColumnType.UNKNOWN.value, ColumnType.BOOLEAN.value},
}


def list_rules(db: Session, dataset_id: int | None = None, active_only: bool = False) -> list[QualityRule]:
    query = db.query(QualityRule)
    if dataset_id is not None:
        query = query.filter(QualityRule.dataset_id == dataset_id)
    if active_only:
        query = query.filter(QualityRule.is_active.is_(True))
    return query.order_by(QualityRule.id.asc()).all()


def _profile_columns(db: Session, dataset_id: int) -> dict[str, ColumnProfile]:
    profiles = db.query(ColumnProfile).filter(ColumnProfile.dataset_id == dataset_id).all()
    return {profile.column_name: profile for profile in profiles}


def _assert_can_edit(actor: User, rule: QualityRule) -> None:
    if actor.role == "analyst" and rule.created_by != actor.id:
        raise AppError(
            ErrorCode.FORBIDDEN,
            message="分析师只能修改自己创建的规则",
            detail={"rule_id": rule.id, "created_by": rule.created_by},
        )


def _check_column(profiles: dict[str, ColumnProfile], column_name: str, rule_type: str) -> None:
    profile = profiles.get(column_name)
    if profile is None:
        raise AppError(
            ErrorCode.RULE_TYPE_MISMATCH,
            message=f"数据集没有列 {column_name}",
            detail={"column_name": column_name, "columns": list(profiles.keys())[:30]},
        )
    allowed = RULE_TYPE_COLUMN_TYPES.get(rule_type)
    if allowed and profile.inferred_type not in allowed:
        raise AppError(
            ErrorCode.RULE_TYPE_MISMATCH,
            message=f"{rule_type} 不能用于 {profile.inferred_type} 类型的列 {column_name}",
            detail={"column_name": column_name, "inferred_type": profile.inferred_type, "allowed": sorted(allowed)},
        )


def create_rule(db: Session, actor: User, payload) -> QualityRule:
    dataset = db.get(Dataset, payload.dataset_id)
    if dataset is None or dataset.is_deleted:
        raise AppError(ErrorCode.DATASET_NOT_FOUND, detail={"dataset_id": payload.dataset_id})
    profiles = _profile_columns(db, dataset.id)
    if not profiles:
        raise AppError(ErrorCode.PROFILE_NOT_READY, detail={"dataset_id": dataset.id})
    _check_column(profiles, payload.column_name, payload.rule_type)
    if payload.rule_type == RuleType.REFERENTIAL.value:
        target_id = (payload.params or {}).get("target_dataset_id")
        target = db.get(Dataset, int(target_id)) if target_id else None
        if target is None or target.is_deleted:
            raise AppError(
                ErrorCode.REFERENTIAL_TARGET_MISSING,
                detail={"target_dataset_id": target_id},
            )
    params = validate_params(payload.rule_type, payload.params, list(profiles.keys()))
    existing = (
        db.query(QualityRule)
        .filter(QualityRule.dataset_id == payload.dataset_id, QualityRule.name == payload.name)
        .first()
    )
    if existing:
        raise AppError(
            ErrorCode.RULE_PARAMS_INVALID,
            message=f"同一数据集下规则名重复：{payload.name}",
            detail={"rule_id": existing.id},
        )
    rule = QualityRule(
        dataset_id=payload.dataset_id,
        name=payload.name,
        rule_type=payload.rule_type,
        column_name=payload.column_name,
        params_json=params,
        severity=payload.severity,
        is_active=payload.is_active,
        sample_limit=payload.sample_limit,
        created_by=actor.id,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    log_event(
        "AUDIT_RULE_CREATE",
        rule_id=rule.id,
        dataset_id=rule.dataset_id,
        rule_type=rule.rule_type,
        column=rule.column_name,
        severity=rule.severity,
    )
    return rule


def update_rule(db: Session, actor: User, rule: QualityRule, payload) -> tuple[QualityRule, dict]:
    _assert_can_edit(actor, rule)
    before = {
        "name": rule.name,
        "rule_type": rule.rule_type,
        "column_name": rule.column_name,
        "params_json": rule.params_json,
        "severity": rule.severity,
        "is_active": rule.is_active,
    }
    profiles = _profile_columns(db, rule.dataset_id)
    rule_type = payload.rule_type or rule.rule_type
    column_name = payload.column_name or rule.column_name
    _check_column(profiles, column_name, rule_type)
    params = validate_params(rule_type, payload.params if payload.params is not None else rule.params_json, list(profiles.keys()))
    if payload.name and payload.name != rule.name:
        clash = (
            db.query(QualityRule)
            .filter(
                QualityRule.dataset_id == rule.dataset_id,
                QualityRule.name == payload.name,
                QualityRule.id != rule.id,
            )
            .first()
        )
        if clash:
            raise AppError(ErrorCode.RULE_PARAMS_INVALID, message="规则名重复", detail={"rule_id": clash.id})
        rule.name = payload.name
    rule.rule_type = rule_type
    rule.column_name = column_name
    rule.params_json = params
    if payload.severity:
        rule.severity = payload.severity
    if payload.is_active is not None:
        rule.is_active = payload.is_active
    if payload.sample_limit is not None:
        rule.sample_limit = payload.sample_limit
    db.commit()
    db.refresh(rule)
    log_event("AUDIT_RULE_UPDATE", rule_id=rule.id, dataset_id=rule.dataset_id, severity=rule.severity)
    return rule, before


def toggle_rule(db: Session, actor: User, rule: QualityRule, is_active: bool) -> tuple[QualityRule, bool]:
    _assert_can_edit(actor, rule)
    before = rule.is_active
    rule.is_active = bool(is_active)
    db.commit()
    db.refresh(rule)
    log_event("AUDIT_RULE_TOGGLE", rule_id=rule.id, is_active=rule.is_active)
    return rule, before


def delete_rule(db: Session, actor: User, rule: QualityRule) -> dict:
    _assert_can_edit(actor, rule)
    before = {"id": rule.id, "name": rule.name, "dataset_id": rule.dataset_id}
    db.query(QualityRule).filter(QualityRule.id == rule.id).delete()
    from app.models import Issue

    db.query(Issue).filter(Issue.rule_id == rule.id).delete()
    db.commit()
    log_event("AUDIT_RULE_DELETE", rule_id=before["id"], dataset_id=before["dataset_id"])
    return before


def recommend(db: Session, dataset_id: int, limit: int = 5) -> list[dict]:
    dataset = db.get(Dataset, dataset_id)
    if dataset is None or dataset.is_deleted:
        raise AppError(ErrorCode.DATASET_NOT_FOUND, detail={"dataset_id": dataset_id})
    profiles = [
        profile
        for profile in db.query(ColumnProfile)
        .filter(ColumnProfile.dataset_id == dataset_id)
        .order_by(ColumnProfile.ordinal.asc())
        .all()
    ]
    if not profiles:
        raise AppError(ErrorCode.PROFILE_NOT_READY, detail={"dataset_id": dataset_id})
    from app.schemas.profile import serialize_column_profile

    serialized = [serialize_column_profile(profile) for profile in profiles]
    return suggest_for_dataset(serialized, dataset.row_count, limit=limit)
