"""Shared contract for every rule validator (one file per rule type)."""
import re
from dataclasses import dataclass, field

import pandas as pd


@dataclass
class RuleContext:
    df: pd.DataFrame
    column: str
    params: dict = field(default_factory=dict)
    target_values: set[str] | None = None
    sample_limit: int = 200


@dataclass
class RuleResult:
    violation_count: int
    samples: list[tuple[int, str, str]]
    expected: str
    # row indexes that violate, capped at 20k — used by recheck_issues to flip
    # previously-open issue rows to `fixed` after a re-run.
    violated_rows: set[int] = field(default_factory=set)
    error_code: str | None = None
    error_message: str | None = None


def null_mask(series: pd.Series) -> pd.Series:
    return series.isna() | (series.astype(str).str.strip() == "")


def text_series(series: pd.Series) -> pd.Series:
    return series.astype(str)


def collect(mask: pd.Series, series: pd.Series, expected: str, limit: int) -> RuleResult:
    """Materialise violation samples from a boolean mask, keeping the raw cell text."""
    total = int(mask.sum())
    matched = series.index[mask]
    indexes = matched[:limit]
    samples = [(int(idx), "" if pd.isna(series.loc[idx]) else str(series.loc[idx]), expected) for idx in indexes]
    violated_rows = {int(idx) for idx in matched[:20000]}
    return RuleResult(
        violation_count=total,
        samples=samples,
        expected=expected,
        violated_rows=violated_rows,
    )


def compile_pattern(pattern: str) -> re.Pattern:
    return re.compile(pattern)
