"""Full-column statistics: null rate, cardinality, quantiles, top values."""
import pandas as pd

from app.constants.column_type import ColumnType, NUMERIC_TYPES
from app.profiling.outliers import iqr_outliers, to_numeric

TOP_VALUE_LIMIT = 10


def null_mask(series: pd.Series) -> pd.Series:
    return series.isna() | (series.astype(str).str.strip() == "")


def compute_stats(series: pd.Series, inferred_type: str, row_count: int) -> dict:
    is_null = null_mask(series)
    null_count = int(is_null.sum())
    non_null = series[~is_null]
    null_rate = round(null_count / row_count, 4) if row_count else 0.0
    distinct_count = int(non_null.nunique())

    min_value = None
    max_value = None
    p50 = None
    p95 = None
    outlier_count = 0
    top_values: list[dict] = []

    if inferred_type in NUMERIC_TYPES:
        numeric = to_numeric(series)
        clean = numeric.dropna()
        if not clean.empty:
            min_value = _format_number(float(clean.min()))
            max_value = _format_number(float(clean.max()))
            p50 = round(float(clean.quantile(0.50)), 6)
            p95 = round(float(clean.quantile(0.95)), 6)
        outlier_count, _, _ = iqr_outliers(numeric)
    elif inferred_type in (ColumnType.DATE.value, ColumnType.BOOLEAN.value):
        if not non_null.empty:
            min_value = str(non_null.min())
            max_value = str(non_null.max())

    if inferred_type not in NUMERIC_TYPES or not top_values:
        counts = non_null.value_counts().head(TOP_VALUE_LIMIT)
        top_values = [{"value": str(index)[:120], "count": int(count)} for index, count in counts.items()]

    return {
        "null_rate": null_rate,
        "null_count": null_count,
        "distinct_count": distinct_count,
        "min_value": min_value,
        "max_value": max_value,
        "p50": p50,
        "p95": p95,
        "outlier_count": outlier_count,
        "top_values": top_values,
    }


def _format_number(value: float) -> str:
    if value.is_integer():
        return str(int(value))
    return f"{value:.6f}".rstrip("0").rstrip(".")
