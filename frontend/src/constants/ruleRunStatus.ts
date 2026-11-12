// RuleRunStatus — mirror of backend/app/constants/rule_run_status.py
export enum RuleRunStatus {
  QUEUED = 'queued',
  RUNNING = 'running',
  SUCCEEDED = 'succeeded',
  FAILED = 'failed',
}

export const RUN_STATUS_LABELS: Record<string, string> = {
  [RuleRunStatus.QUEUED]: '排队中',
  [RuleRunStatus.RUNNING]: '执行中',
  [RuleRunStatus.SUCCEEDED]: '已完成',
  [RuleRunStatus.FAILED]: '失败',
}

export const RUN_TERMINAL_STATUSES = [RuleRunStatus.SUCCEEDED, RuleRunStatus.FAILED]
