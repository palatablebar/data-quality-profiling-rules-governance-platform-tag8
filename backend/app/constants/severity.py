"""Severity — backend source of truth, mirrored by frontend/src/constants/severity.ts."""
from enum import Enum


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


ALL_SEVERITIES = [s.value for s in Severity]
SEVERITY_WEIGHT = {Severity.LOW.value: 1, Severity.MEDIUM.value: 2, Severity.HIGH.value: 3, Severity.CRITICAL.value: 4}
SEVERITY_LABELS = {
    Severity.LOW.value: "低",
    Severity.MEDIUM.value: "中",
    Severity.HIGH.value: "高",
    Severity.CRITICAL.value: "严重",
}
