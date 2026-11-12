"""regex: whole-value match against a user supplied pattern (nulls are skipped)."""
from app.constants.error_codes import AppError, ErrorCode
from app.constants.rule_type import RuleType
from app.rules.base import RuleContext, RuleResult, collect, null_mask

RULE_TYPE = RuleType.REGEX.value
LABEL = "正则"


def check(ctx: RuleContext) -> RuleResult:
    pattern = str((ctx.params or {}).get("pattern") or "")
    try:
        matched = ctx.df[ctx.column].astype(str).str.fullmatch(pattern, na=False)
    except Exception as exc:  # invalid regex should have been caught at save time
        raise AppError(ErrorCode.EXPRESSION_SYNTAX, detail={"pattern": pattern, "error": str(exc)}) from exc
    mask = ~matched & ~null_mask(ctx.df[ctx.column])
    expected = f"{ctx.column} ~ {pattern}"
    return collect(mask, ctx.df[ctx.column], expected, ctx.sample_limit)
