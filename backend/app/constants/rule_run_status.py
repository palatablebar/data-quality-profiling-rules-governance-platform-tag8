"""RuleRunStatus — backend source of truth, mirrored by frontend/src/constants/ruleRunStatus.ts."""
from enum import Enum


class RuleRunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


ALL_RUN_STATUSES = [s.value for s in RuleRunStatus]
TERMINAL_STATUSES = {RuleRunStatus.SUCCEEDED.value, RuleRunStatus.FAILED.value}

# RuleRun.kind: profile runs and rule runs share the same id sequence so the
# UI can align a profiling batch with a rule batch.
class RunKind(str, Enum):
    PROFILE = "profile"
    RULES = "rules"
