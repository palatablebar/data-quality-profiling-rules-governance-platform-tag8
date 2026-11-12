"""Audit payload helper shared by controllers (keeps controller files thin)."""
from app.middlewares.audit_logger import record


def audit_event(request, action: str, entity_type: str, entity_id, before=None, after=None) -> None:
    record(request, action, entity_type, entity_id, before, after)
