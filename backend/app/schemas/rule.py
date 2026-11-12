from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from app.constants.rule_type import ALL_RULE_TYPES
from app.schemas.common import iso
from app.utils.formatters import rule_param_summary, rule_type_label, severity_label

RuleTypeLiteral = Literal[
    "not_null",
    "unique",
    "range",
    "regex",
    "enum_set",
    "referential",
    "expression",
]
SeverityLiteral = Literal["low", "medium", "high", "critical"]


class RuleCreate(BaseModel):
    dataset_id: int
    name: str = Field(min_length=1, max_length=190)
    rule_type: RuleTypeLiteral
    column_name: str = Field(min_length=1, max_length=190)
    params: dict[str, Any] = Field(default_factory=dict)
    severity: SeverityLiteral = "medium"
    is_active: bool = True
    sample_limit: int = Field(default=200, ge=1, le=5000)

    @field_validator("rule_type")
    @classmethod
    def _known_rule_type(cls, value: str) -> str:
        if value not in ALL_RULE_TYPES:
            raise ValueError("未知规则类型")
        return value


class RuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=190)
    rule_type: RuleTypeLiteral | None = None
    column_name: str | None = Field(default=None, min_length=1, max_length=190)
    params: dict[str, Any] | None = None
    severity: SeverityLiteral | None = None
    is_active: bool | None = None
    sample_limit: int | None = Field(default=None, ge=1, le=5000)


class BulkRunRequest(BaseModel):
    dataset_id: int
    rule_ids: list[int] | None = None


def serialize_rule(rule, reporter: dict | None = None) -> dict:
    return {
        "id": rule.id,
        "dataset_id": rule.dataset_id,
        "name": rule.name,
        "rule_type": rule.rule_type,
        "rule_type_label": rule_type_label(rule.rule_type),
        "column_name": rule.column_name,
        "params": rule.params_json or {},
        "param_summary": rule_param_summary(rule.rule_type, rule.params_json or {}),
        "severity": rule.severity,
        "severity_label": severity_label(rule.severity),
        "is_active": rule.is_active,
        "sample_limit": rule.sample_limit,
        "created_by": rule.created_by,
        "created_at": iso(rule.created_at),
        "updated_at": iso(rule.updated_at),
        "last_result": reporter,
    }
