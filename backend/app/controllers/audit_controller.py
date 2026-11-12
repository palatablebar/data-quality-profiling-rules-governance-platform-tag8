from sqlalchemy.orm import Session

from app.models import AuditLog, User


def recent(db: Session, limit: int = 10) -> dict:
    rows = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(limit).all()
    actors = {user.id: user.display_name for user in db.query(User).all()}
    return {
        "items": [
            {
                "id": row.id,
                "actor_id": row.actor_id,
                "actor_name": actors.get(row.actor_id),
                "action": row.action,
                "entity_type": row.entity_type,
                "entity_id": row.entity_id,
                "before_json": row.before_json,
                "after_json": row.after_json,
                "ip": row.ip,
                "created_at": row.created_at.strftime("%Y-%m-%d %H:%M:%S") if row.created_at else None,
            }
            for row in rows
        ]
    }
