from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.controllers import profile_controller
from app.middlewares.auth import get_current_user
from app.middlewares.rbac import require_roles
from app.models import User

router = APIRouter(prefix="/datasets", tags=["profiles"])


@router.get("/{dataset_id}/profile")
def get_profile(dataset_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return profile_controller.get_profile(db, dataset_id)


@router.post("/{dataset_id}/profile")
def start_profile(
    dataset_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("steward", "analyst")),
):
    return profile_controller.start_profile(request, db, user, dataset_id)


@router.get("/{dataset_id}/columns")
def get_columns(dataset_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return profile_controller.get_columns(db, dataset_id)


@router.get("/{dataset_id}/recommendations")
def recommendations(
    dataset_id: int,
    limit: int = 5,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return profile_controller.recommend(db, dataset_id, limit=limit)
