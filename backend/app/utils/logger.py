"""The only logging entry point. ``log_event`` renders a template from
constants/log_templates.py and collapses missing fields to ``-`` so a log line
never explodes.
"""
import json
import logging
import sys

from app.constants.log_templates import LOG_TEMPLATES

logger = logging.getLogger("qualiscope")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


class _SafeDict(dict):
    def __missing__(self, key):  # noqa: D105
        return "-"


def log_event(key: str, level: int = logging.INFO, **fields):
    template = LOG_TEMPLATES.get(key, key + " " + " ".join(f"{k}={{{k}}}" for k in fields))
    try:
        line = template.format_map(_SafeDict({k: v for k, v in fields.items() if v is not None}))
    except Exception:
        line = f"{key} {json.dumps(fields, default=str)}"
    logger.log(level, "event=%s %s", key, line)
