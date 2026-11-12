// RuleRunStatus — mirror of backend/app/constants/rule_run_status.py
export enum RuleRunStatus {
  QUEUED = 'queued',
  RUNNING = 'running',
  SUCCEEDED = 'succeeded',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

export const RUN_STATUS_LABELS: Record<string, string> = {
  [RuleRunStatus.QUEUED]: '排队中',
  [RuleRunStatus.RUNNING]: '执行中',
  [RuleRunStatus.SUCCEEDED]: '已完成',
  [RuleRunStatus.FAILED]: '失败',
  [RuleRunStatus.CANCELLED]: '已中止',
}

export const RUN_TERMINAL_STATUSES = [RuleRunStatus.SUCCEEDED, RuleRunStatus.FAILED, RuleRunStatus.CANCELLED]

// RuleRunItem.status — a rule the batch never reached is a cancelled placeholder
export const RUN_ITEM_STATUS = {
  FINISHED: 'finished',
  CANCELLED: 'cancelled',
} as const
