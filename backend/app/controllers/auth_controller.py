from sqlalchemy.orm import Session

from app.middlewares.quota import quota_snapshot
from app.models import User
from app.schemas.auth import serialize_user
from app.services import auth_service


def login(db: Session, payload) -> dict:
    user, token = auth_service.authenticate(db, payload.email, payload.password)
    return {
        "token": token,
        "token_type": "bearer",
        "user": {**serialize_user(user), "quota": quota_snapshot(user)},
    }


def me(user: User) -> dict:
    return {"user": {**serialize_user(user), "quota": quota_snapshot(user)}}
