from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.controllers import rule_controller
from app.middlewares.auth import get_current_user
from app.middlewares.rbac import require_roles
from app.models import User
from app.schemas.rule import RuleCreate, RuleUpdate

router = APIRouter(prefix="/rules", tags=["rules"])


@router.get("")
def list_rules(
    dataset_id: int | None = None,
    active_only: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return rule_controller.list_rules(db, dataset_id, active_only)


@router.post("")
def create_rule(
    payload: RuleCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("steward", "analyst")),
):
    return rule_controller.create_rule(request, db, user, payload)


@router.patch("/{rule_id}")
def update_rule(
    rule_id: int,
    payload: RuleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("steward", "analyst")),
):
    return rule_controller.update_rule(request, db, user, rule_id, payload)


@router.post("/{rule_id}/toggle")
def toggle_rule(
    rule_id: int,
    request: Request,
    is_active: bool = True,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("steward", "analyst")),
):
    return rule_controller.toggle_rule(request, db, user, rule_id, is_active)


@router.delete("/{rule_id}")
def delete_rule(
    rule_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("steward", "analyst")),
):
    return rule_controller.delete_rule(request, db, user, rule_id)
