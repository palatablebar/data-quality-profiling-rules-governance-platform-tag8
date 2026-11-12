"""not_null: empty string or NULL counts as a violation."""
from app.constants.rule_type import RuleType
from app.rules.base import RuleContext, RuleResult, collect, null_mask

RULE_TYPE = RuleType.NOT_NULL.value
LABEL = "非空"


def check(ctx: RuleContext) -> RuleResult:
    series = ctx.df[ctx.column]
    mask = null_mask(series)
    expected = f"{ctx.column} IS NOT NULL"
    return collect(mask, series, expected, ctx.sample_limit)
