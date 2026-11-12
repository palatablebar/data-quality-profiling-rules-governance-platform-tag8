from sqlalchemy.orm import Session

from app.models import User
from app.schemas.auth import serialize_user


def list_users(db: Session) -> dict:
    users = db.query(User).order_by(User.id.asc()).all()
    return {"items": [serialize_user(user) for user in users], "total": len(users)}
