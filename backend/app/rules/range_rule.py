"""range: numeric value must fall inside [min, max]; non-numeric cells violate."""
import pandas as pd

from app.constants.rule_type import RuleType
from app.profiling.outliers import to_numeric
from app.rules.base import RuleContext, RuleResult, collect

RULE_TYPE = RuleType.RANGE.value
LABEL = "范围"


def check(ctx: RuleContext) -> RuleResult:
    series = ctx.df[ctx.column]
    numeric = to_numeric(series)
    mask = pd.Series(False, index=series.index)
    low = ctx.params.get("min")
    high = ctx.params.get("max")
    if low is not None:
        mask |= numeric < float(low)
    if high is not None:
        mask |= numeric > float(high)
    expected = f"{ctx.column} BETWEEN {low if low is not None else '-inf'} AND {high if high is not None else 'inf'}"
    return collect(mask, series, expected, ctx.sample_limit)
