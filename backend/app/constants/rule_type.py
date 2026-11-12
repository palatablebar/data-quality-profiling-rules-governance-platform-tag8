"""RuleType — backend source of truth, mirrored by frontend/src/constants/ruleType.ts.

Consumed by: rules/registry.py (dispatch table), schemas/rule.py (Literal),
rules/*.py validators, utils/formatters.py, constants/error_codes.py,
constants/log_templates.py, services/rule_service.py.
"""
from enum import Enum


class RuleType(str, Enum):
    NOT_NULL = "not_null"
    UNIQUE = "unique"
    RANGE = "range"
    REGEX = "regex"
    ENUM_SET = "enum_set"
    REFERENTIAL = "referential"
    EXPRESSION = "expression"


ALL_RULE_TYPES = [t.value for t in RuleType]

# rule_type -> the JSON keys that params_json must carry
PARAM_KEYS = {
    RuleType.NOT_NULL.value: [],
    RuleType.UNIQUE.value: [],
    RuleType.RANGE.value: ["min", "max"],
    RuleType.REGEX.value: ["pattern"],
    RuleType.ENUM_SET.value: ["values"],
    RuleType.REFERENTIAL.value: ["target_dataset_id", "target_column"],
    RuleType.EXPRESSION.value: ["expr"],
}
