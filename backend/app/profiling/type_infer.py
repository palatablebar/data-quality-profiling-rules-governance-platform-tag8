"""Column type inference.

Samples the first 10,000 non-empty values and picks the first candidate type
whose hit rate reaches 0.95; otherwise falls back to ``string``. A column with
no non-empty values is ``unknown``. Mirrored by frontend constants/columnType.ts.
"""
import re
from datetime import datetime

from app.constants.column_type import ColumnType

SAMPLE_SIZE = 10_000
HIT_THRESHOLD = 0.95

INT_RE = re.compile(r"^-?\d+$")
DECIMAL_RE = re.compile(r"^-?\d+\.\d+$|^-?\.\d+$")
DATE_RES = [
    re.compile(r"^\d{4}-\d{2}-\d{2}$"),
    re.compile(r"^\d{4}/\d{2}/\d{2}$"),
    re.compile(r"^\d{8}$"),
]
BOOLEAN_TOKENS = {"true", "false", "yes", "no", "y", "n", "t", "f"}


def _is_int(value: str) -> bool:
    return bool(INT_RE.match(value))


def _is_decimal(value: str) -> bool:
    if DECIMAL_RE.match(value):
        return True
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def _is_date(value: str) -> bool:
    for pattern in DATE_RES:
        if pattern.match(value):
            for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
                try:
                    datetime.strptime(value, fmt)
                    return True
                except ValueError:
                    continue
    return False


def _is_boolean(value: str) -> bool:
    return value.strip().lower() in BOOLEAN_TOKENS


CANDIDATES = [
    (ColumnType.INTEGER.value, _is_int),
    (ColumnType.DECIMAL.value, _is_decimal),
    (ColumnType.DATE.value, _is_date),
    (ColumnType.BOOLEAN.value, _is_boolean),
]


def sample_values(values, limit: int = SAMPLE_SIZE) -> list[str]:
    picked: list[str] = []
    for value in values:
        text = "" if value is None else str(value)
        if text == "":
            continue
        picked.append(text)
        if len(picked) >= limit:
            break
    return picked


def infer_type(values) -> str:
    sample = sample_values(values)
    if not sample:
        return ColumnType.UNKNOWN.value
    total = len(sample)
    for type_name, predicate in CANDIDATES:
        hits = sum(1 for value in sample if predicate(value))
        if hits / total >= HIT_THRESHOLD:
            if type_name == ColumnType.INTEGER.value and _looks_like_identifier(sample):
                # 18-digit account/certificate numbers are identifiers, not measures
                return ColumnType.STRING.value
            return type_name
    return ColumnType.STRING.value


def _looks_like_identifier(sample: list[str]) -> bool:
    digits = [value.lstrip("-") for value in sample]
    if digits and all(len(value) >= 15 for value in digits):
        return True
    return any(len(value) > 1 and value.startswith("0") for value in digits)
