"""unique: every non-empty value may appear exactly once."""
from app.constants.rule_type import RuleType
from app.rules.base import RuleContext, RuleResult, collect, null_mask

RULE_TYPE = RuleType.UNIQUE.value
LABEL = "唯一"


def check(ctx: RuleContext) -> RuleResult:
    series = ctx.df[ctx.column]
    duplicates = series.duplicated(keep=False) & ~null_mask(series)
    expected = f"{ctx.column} IS UNIQUE"
    return collect(duplicates, series, expected, ctx.sample_limit)
