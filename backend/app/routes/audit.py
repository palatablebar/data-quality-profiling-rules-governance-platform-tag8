from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.controllers import audit_controller
from app.middlewares.auth import get_current_user
from app.models import User

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/recent")
def recent(limit: int = 10, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return audit_controller.recent(db, limit)
