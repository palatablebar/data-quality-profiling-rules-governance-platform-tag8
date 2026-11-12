"""Formatting helpers used by controller serialisation, audit payloads, worker
logs and the report export. Deliberately multi-purpose: row counts, ratios,
percentiles, durations, rule-parameter summaries and enum labels all live here.
"""
from app.constants.column_type import ColumnType
from app.constants.messages import COLUMN_TYPE_LABELS
from app.constants.rule_type import RuleType
from app.constants.severity import SEVERITY_LABELS

TYPE_LABELS = COLUMN_TYPE_LABELS

RULE_TYPE_LABELS = {
    RuleType.NOT_NULL.value: "非空",
    RuleType.UNIQUE.value: "唯一",
    RuleType.RANGE.value: "范围",
    RuleType.REGEX.value: "正则",
    RuleType.ENUM_SET.value: "枚举",
    RuleType.REFERENTIAL.value: "引用",
    RuleType.EXPRESSION.value: "表达式",
}


def fmt_int(value) -> str:
    if value is None:
        return "-"
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return str(value)


def fmt_rate(value) -> str:
    if value is None:
        return "-"
    return f"{float(value) * 100:.2f}%"


def fmt_percentile(value) -> str:
    if value is None:
        return "-"
    if isinstance(value, float) and value.is_integer():
        return f"{int(value):,}"
    return f"{value:,.4f}".rstrip("0").rstrip(".") if isinstance(value, float) else str(value)


def fmt_duration(ms) -> str:
    if ms is None:
        return "-"
    ms = int(ms)
    if ms < 1000:
        return f"{ms} ms"
    return f"{ms / 1000:.2f} s"


def type_label(inferred_type: str | None) -> str:
    return TYPE_LABELS.get(inferred_type or ColumnType.UNKNOWN.value, "未知")


def severity_label(severity: str | None) -> str:
    return SEVERITY_LABELS.get(severity or "", "-")


def rule_type_label(rule_type: str | None) -> str:
    return RULE_TYPE_LABELS.get(rule_type or "", "-")


def rule_param_summary(rule_type: str, params: dict | None) -> str:
    params = params or {}
    if rule_type == RuleType.RANGE.value:
        return f"min={params.get('min', '-∞')} max={params.get('max', '+∞')}"
    if rule_type == RuleType.REGEX.value:
        return f"pattern={params.get('pattern', '')}"
    if rule_type == RuleType.ENUM_SET.value:
        values = params.get("values") or []
        head = ", ".join(str(v) for v in values[:5])
        more = f" +{len(values) - 5}" if len(values) > 5 else ""
        return f"values=[{head}{more}]"
    if rule_type == RuleType.REFERENTIAL.value:
        return (
            f"target_dataset={params.get('target_dataset_id', '?')}."
            f"{params.get('target_column', '?')}"
        )
    if rule_type == RuleType.EXPRESSION.value:
        return f"expr={params.get('expr', '')}"
    return "-"


def expected_expression(rule_type: str, params: dict | None, column: str) -> str:
    params = params or {}
    if rule_type == RuleType.NOT_NULL.value:
        return f"{column} IS NOT NULL"
    if rule_type == RuleType.UNIQUE.value:
        return f"{column} IS UNIQUE"
    if rule_type == RuleType.RANGE.value:
        return f"{column} BETWEEN {params.get('min', '-inf')} AND {params.get('max', 'inf')}"
    if rule_type == RuleType.REGEX.value:
        return f"{column} ~ {params.get('pattern', '')}"
    if rule_type == RuleType.ENUM_SET.value:
        return f"{column} IN ({', '.join(str(v) for v in (params.get('values') or []))})"
    if rule_type == RuleType.REFERENTIAL.value:
        return f"{column} REFERENCES dataset#{params.get('target_dataset_id')}.{params.get('target_column')}"
    if rule_type == RuleType.EXPRESSION.value:
        return f"{params.get('expr', '')}"
    return f"{column}"


def percentile_positions(p50, p95, min_value, max_value) -> dict:
    """Normalised 0..1 anchors used by <PercentileScale>."""
    try:
        lo = float(min_value)
        hi = float(max_value)
    except (TypeError, ValueError):
        return {"p50": None, "p95": None}
    if hi <= lo:
        return {"p50": 0.0, "p95": 0.0}
    span = hi - lo
    return {
        "p50": 0.0 if p50 is None else round((float(p50) - lo) / span, 4),
        "p95": 0.0 if p95 is None else round((float(p95) - lo) / span, 4),
    }
