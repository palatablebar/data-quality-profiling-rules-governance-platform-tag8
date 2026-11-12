"""enum_set: value must be one of the allowed enumeration values."""
from app.constants.rule_type import RuleType
from app.rules.base import RuleContext, RuleResult, collect, null_mask

RULE_TYPE = RuleType.ENUM_SET.value
LABEL = "枚举"


def check(ctx: RuleContext) -> RuleResult:
    series = ctx.df[ctx.column]
    allowed = {str(value) for value in (ctx.params or {}).get("values") or []}
    mask = ~series.astype(str).isin(allowed) & ~null_mask(series)
    expected = f"{ctx.column} IN ({', '.join(sorted(allowed))})"
    return collect(mask, series, expected, ctx.sample_limit)
