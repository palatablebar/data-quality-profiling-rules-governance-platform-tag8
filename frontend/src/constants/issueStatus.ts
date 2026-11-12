// IssueStatus — mirror of backend/app/constants/issue_status.py
export enum IssueStatus {
  OPEN = 'open',
  TRIAGED = 'triaged',
  FIXED = 'fixed',
  IGNORED = 'ignored',
}

export const ISSUE_STATUS_LABELS: Record<string, string> = {
  [IssueStatus.OPEN]: '待分诊',
  [IssueStatus.TRIAGED]: '已指派',
  [IssueStatus.FIXED]: '已修复',
  [IssueStatus.IGNORED]: '已忽略',
}

export const ISSUE_STATUS_LIST = [
  IssueStatus.OPEN,
  IssueStatus.TRIAGED,
  IssueStatus.FIXED,
  IssueStatus.IGNORED,
]
