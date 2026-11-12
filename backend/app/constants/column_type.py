"""ColumnType — the single backend source of truth for inferred column types.

Consumed by: profiling/type_infer.py, profiling/stats.py, profiling/suggest.py,
schemas/profile.py, services/profile_service.py, utils/formatters.py,
constants/messages.py, constants/log_templates.py.
Mirror of frontend/src/constants/columnType.ts.
"""
from enum import Enum


class ColumnType(str, Enum):
    INTEGER = "integer"
    DECIMAL = "decimal"
    STRING = "string"
    DATE = "date"
    BOOLEAN = "boolean"
    UNKNOWN = "unknown"


NUMERIC_TYPES = {ColumnType.INTEGER.value, ColumnType.DECIMAL.value}
TEXT_TYPES = {ColumnType.STRING.value, ColumnType.UNKNOWN.value}
ALL_TYPES = [t.value for t in ColumnType]
