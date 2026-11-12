from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.controllers import auth_controller, user_controller
from app.middlewares.auth import get_current_user
from app.models import User
from app.schemas.auth import LoginRequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    return auth_controller.login(db, payload)


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return auth_controller.me(user)


@router.get("/users")
def list_users(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return user_controller.list_users(db)
