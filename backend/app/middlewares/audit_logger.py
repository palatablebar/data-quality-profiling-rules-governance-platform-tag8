"""Response-phase audit writer.

Controllers call ``record(request, action, ...)`` after a successful write; this
middleware then writes the audit rows (with before/after snapshots) once the
response status is known. A failure to write is logged, never propagated.
"""
from starlette.middleware.base import BaseHTTPMiddleware

from app.config.database import SessionLocal
from app.models import AuditLog
from app.utils.logger import log_event


def record(request, action: str, entity_type: str, entity_id=None, before=None, after=None) -> None:
    events = getattr(request.state, "audit_events", None)
    if events is None:
        events = []
        request.state.audit_events = events
    claims = getattr(request.state, "user_claims", None) or {}
    events.append(
        {
            "actor_id": int(claims.get("sub")) if claims.get("sub") else None,
            "action": action,
            "entity_type": entity_type,
            "entity_id": int(entity_id) if entity_id is not None else None,
            "before_json": before,
            "after_json": after,
            "ip": request.client.host if request.client else None,
        }
    )


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request.state.audit_events = []
        response = await call_next(request)
        events = getattr(request.state, "audit_events", []) or []
        if events and response.status_code < 400:
            self._persist(events)
        return response

    @staticmethod
    def _persist(events: list[dict]) -> None:
        db = SessionLocal()
        try:
            for event in events:
                db.add(AuditLog(**event))
            db.commit()
        except Exception as exc:  # pragma: no cover - audit must never break the request
            db.rollback()
            log_event(
                "AUDIT_WRITE_FAILED",
                action=events[0].get("action", "?"),
                entity_type=events[0].get("entity_type", "?"),
                reason=str(exc),
            )
        finally:
            db.close()
