"""RuleType dispatch table + parameter validation.

Adding a rule type means touching this table, a new validator module, the
schema Literal, the frontend constant, the param form and the serialiser.
"""
from app.constants.error_codes import AppError, ErrorCode
from app.constants.rule_type import PARAM_KEYS, RuleType

CHECKERS = {}
DESCRIPTIONS = {
    RuleType.NOT_NULL.value: "列值不允许为空",
    RuleType.UNIQUE.value: "列值在数据集内唯一",
    RuleType.RANGE.value: "数值落在 [min, max] 区间",
    RuleType.REGEX.value: "整值匹配正则",
    RuleType.ENUM_SET.value: "取值属于枚举集合",
    RuleType.REFERENTIAL.value: "取值必须存在于目标数据集的目标列",
    RuleType.EXPRESSION.value: "白名单表达式为真",
}


def _load() -> None:
    if CHECKERS:
        return
    from app.rules import (
        enum_set,
        expression,
        not_null,
        range_rule,
        referential,
        regex_rule,
        unique,
    )

    CHECKERS.update(
        {
            RuleType.NOT_NULL.value: not_null.check,
            RuleType.UNIQUE.value: unique.check,
            RuleType.RANGE.value: range_rule.check,
            RuleType.REGEX.value: regex_rule.check,
            RuleType.ENUM_SET.value: enum_set.check,
            RuleType.REFERENTIAL.value: referential.check,
            RuleType.EXPRESSION.value: expression.check,
        }
    )


def get_checker(rule_type: str):
    _load()
    checker = CHECKERS.get(rule_type)
    if checker is None:
        raise AppError(ErrorCode.RULE_PARAMS_INVALID, message=f"未知的规则类型 {rule_type}")
    return checker


def validate_params(rule_type: str, params: dict | None, columns: list[str] | None = None) -> dict:
    _load()
    params = dict(params or {})
    if rule_type not in PARAM_KEYS:
        raise AppError(ErrorCode.RULE_PARAMS_INVALID, message=f"未知的规则类型 {rule_type}")
    for key in PARAM_KEYS[rule_type]:
        if key not in params or params[key] in (None, "", []):
            raise AppError(
                ErrorCode.RULE_PARAMS_INVALID,
                message=f"{rule_type} 缺少参数 {key}",
                detail={"missing": key},
            )
    if rule_type == RuleType.RANGE.value:
        try:
            low = float(params["min"])
            high = float(params["max"])
        except (TypeError, ValueError) as exc:
            raise AppError(ErrorCode.RULE_PARAMS_INVALID, message="范围参数必须是数字") from exc
        if low > high:
            raise AppError(ErrorCode.RULE_PARAMS_INVALID, message="min 不能大于 max")
        params["min"], params["max"] = low, high
    if rule_type == RuleType.REGEX.value:
        from app.rules.base import compile_pattern

        try:
            compile_pattern(str(params["pattern"]))
        except Exception as exc:
            raise AppError(
                ErrorCode.RULE_PARAMS_INVALID,
                message="正则表达式无法编译",
                detail={"pattern": params["pattern"], "error": str(exc)},
            ) from exc
    if rule_type == RuleType.ENUM_SET.value:
        values = params.get("values")
        if not isinstance(values, list) or not values:
            raise AppError(ErrorCode.RULE_PARAMS_INVALID, message="枚举值必须是非空数组")
        params["values"] = [str(v) for v in values]
    if rule_type == RuleType.REFERENTIAL.value:
        try:
            params["target_dataset_id"] = int(params["target_dataset_id"])
        except (TypeError, ValueError) as exc:
            raise AppError(ErrorCode.RULE_PARAMS_INVALID, message="target_dataset_id 必须是整数") from exc
        params["target_column"] = str(params["target_column"])
    if rule_type == RuleType.EXPRESSION.value:
        from app.rules.expression import validate_expression

        validate_expression(str(params["expr"]), columns)
    return params
