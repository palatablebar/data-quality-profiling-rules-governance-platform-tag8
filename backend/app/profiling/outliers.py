"""IQR (1.5x) outlier counting for numeric columns."""
import pandas as pd


def to_numeric(series: pd.Series) -> pd.Series:
    cleaned = series.where(series.str.strip() != "", None)
    return pd.to_numeric(cleaned, errors="coerce")


def iqr_outliers(numeric: pd.Series) -> tuple[int, float | None, float | None]:
    values = numeric.dropna()
    if values.empty:
        return 0, None, None
    q1 = float(values.quantile(0.25))
    q3 = float(values.quantile(0.75))
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    count = int(((values < lower) | (values > upper)).sum())
    return count, lower, upper
