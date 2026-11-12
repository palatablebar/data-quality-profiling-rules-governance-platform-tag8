"""referential: value must exist in the target dataset's target column.

The engine loads the target column into ``ctx.target_values`` (set difference).
"""
from app.constants.rule_type import RuleType
from app.rules.base import RuleContext, RuleResult, collect, null_mask

RULE_TYPE = RuleType.REFERENTIAL.value
LABEL = "引用"


def check(ctx: RuleContext) -> RuleResult:
    series = ctx.df[ctx.column]
    target = ctx.target_values or set()
    mask = ~series.astype(str).isin(target) & ~null_mask(series)
    params = ctx.params or {}
    expected = (
        f"{ctx.column} REFERENCES dataset#{params.get('target_dataset_id')}."
        f"{params.get('target_column')}"
    )
    return collect(mask, series, expected, ctx.sample_limit)
