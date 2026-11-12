"""Shared response envelopes / serialisation helpers."""
from datetime import date, datetime


def iso(value: datetime | date | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return value.strftime("%Y-%m-%d")


def error_envelope(code: str, message: str, request_id: str | None, detail=None) -> dict:
    return {"code": code, "message": message, "detail": detail, "request_id": request_id}
