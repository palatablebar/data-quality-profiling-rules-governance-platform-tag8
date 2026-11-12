from app.constants.column_type import ColumnType
from app.schemas.common import iso
from app.utils.formatters import (
    fmt_int,
    fmt_percentile,
    fmt_rate,
    percentile_positions,
    type_label,
)


def serialize_column_profile(profile) -> dict:
    return {
        "id": profile.id,
        "dataset_id": profile.dataset_id,
        "run_id": profile.run_id,
        "column_name": profile.column_name,
        "ordinal": profile.ordinal,
        "inferred_type": profile.inferred_type,
        "type_label": type_label(profile.inferred_type),
        "null_rate": float(profile.null_rate or 0),
        "null_rate_display": fmt_rate(profile.null_rate),
        "distinct_count": profile.distinct_count,
        "distinct_display": fmt_int(profile.distinct_count),
        "min_value": profile.min_value,
        "max_value": profile.max_value,
        "p50": profile.p50,
        "p95": profile.p95,
        "p50_display": fmt_percentile(profile.p50),
        "p95_display": fmt_percentile(profile.p95),
        "top_values": profile.top_values_json or [],
        "pattern_summary": profile.pattern_summary,
        "outlier_count": profile.outlier_count,
        "percentile_positions": percentile_positions(
            profile.p50, profile.p95, profile.min_value, profile.max_value
        ),
        "is_numeric": profile.inferred_type in {ColumnType.INTEGER.value, ColumnType.DECIMAL.value},
        "created_at": iso(profile.created_at),
    }
