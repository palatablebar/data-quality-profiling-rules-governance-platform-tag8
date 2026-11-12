"""IssueStatus — backend source of truth, mirrored by frontend/src/constants/issueStatus.ts."""
from enum import Enum


class IssueStatus(str, Enum):
    OPEN = "open"
    TRIAGED = "triaged"
    FIXED = "fixed"
    IGNORED = "ignored"


ALL_ISSUE_STATUSES = [s.value for s in IssueStatus]

# legal state machine; `fixed` is also reachable from recheck_issues
TRANSITIONS = {
    IssueStatus.OPEN.value: {IssueStatus.TRIAGED.value, IssueStatus.FIXED.value, IssueStatus.IGNORED.value},
    IssueStatus.TRIAGED.value: {IssueStatus.FIXED.value, IssueStatus.IGNORED.value, IssueStatus.OPEN.value},
    IssueStatus.FIXED.value: {IssueStatus.OPEN.value},
    IssueStatus.IGNORED.value: {IssueStatus.OPEN.value},
}
