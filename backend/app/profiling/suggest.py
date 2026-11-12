"""Turn a column profile into candidate rules for the rule builder."""
from app.constants.column_type import ColumnType, NUMERIC_TYPES
from app.constants.rule_type import RuleType
from app.constants.severity import Severity
from app.profiling.pattern import primary_pattern


def suggest_for_column(profile: dict, row_count: int) -> list[dict]:
    suggestions: list[dict] = []
    column = profile["column_name"]
    null_rate = float(profile.get("null_rate") or 0)
    distinct = int(profile.get("distinct_count") or 0)
    inferred = profile.get("inferred_type") or ColumnType.UNKNOWN.value

    if null_rate > 0:
        suggestions.append(
            {
                "rule_type": RuleType.NOT_NULL.value,
                "column_name": column,
                "params": {},
                "severity": Severity.CRITICAL.value if null_rate > 0.005 else Severity.HIGH.value,
                "reason": f"空值率 {null_rate * 100:.2f}%，需要非空约束",
            }
        )

    if row_count and distinct == row_count and inferred != ColumnType.UNKNOWN.value:
        suggestions.append(
            {
                "rule_type": RuleType.UNIQUE.value,
                "column_name": column,
                "params": {},
                "severity": Severity.HIGH.value,
                "reason": f"基数等于行数（{distinct}），适合做唯一性校验",
            }
        )

    if inferred in NUMERIC_TYPES and profile.get("min_value") is not None:
        try:
            low = float(profile["min_value"])
            high = float(profile["max_value"]) if profile.get("max_value") is not None else low
        except (TypeError, ValueError):
            low = high = None
        if low is not None:
            suggestions.append(
                {
                    "rule_type": RuleType.RANGE.value,
                    "column_name": column,
                    "params": {"min": min(low, 0.0), "max": round(high * 1.2 + 1, 2)},
                    "severity": Severity.HIGH.value if low < 0 else Severity.MEDIUM.value,
                    "reason": f"观测范围 {profile.get('min_value')} ~ {profile.get('max_value')}",
                }
            )

    if inferred == ColumnType.STRING.value:
        pattern = primary_pattern([tv["value"] for tv in profile.get("top_values") or []])
        if pattern:
            suggestions.append(
                {
                    "rule_type": RuleType.REGEX.value,
                    "column_name": column,
                    "params": {"pattern": pattern},
                    "severity": Severity.MEDIUM.value,
                    "reason": f"主模式 {pattern}",
                }
            )

    if inferred in (ColumnType.STRING.value, ColumnType.UNKNOWN.value) and 0 < distinct <= 20:
        values = [tv["value"] for tv in profile.get("top_values") or []]
        if values:
            suggestions.append(
                {
                    "rule_type": RuleType.ENUM_SET.value,
                    "column_name": column,
                    "params": {"values": values},
                    "severity": Severity.MEDIUM.value,
                    "reason": f"低基数（{distinct}），适合做枚举约束",
                }
            )
    return suggestions


def suggest_for_dataset(profiles: list[dict], row_count: int, limit: int = 5) -> list[dict]:
    collected: list[dict] = []
    for profile in profiles:
        collected.extend(suggest_for_column(profile, row_count))
        if len(collected) >= limit:
            break
    return collected[:limit]
