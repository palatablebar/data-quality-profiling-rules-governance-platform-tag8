export interface RunItem {
  id: number
  rule_id: number | null
  rule_name: string
  rule_type: string
  column_name: string
  severity: string
  status: string
  passed: boolean
  violation_count: number
  persisted_count: number
  duration_ms: number
  duration_display: string
  error_code: string | null
}

export interface RuleRun {
  id: number
  dataset_id: number
  dataset_name: string | null
  dataset_format: string | null
  kind: string
  triggered_by: number | null
  status: string
  rules_total: number
  rules_passed: number
  rules_failed: number
  rules_unfinished: number
  rows_scanned: number
  rows_scanned_display: string
  duration_ms: number
  duration_display: string
  report_no: string | null
  error_code: string | null
  started_at: string | null
  finished_at: string | null
  created_at: string | null
}

export interface RunDetail extends RuleRun {
  items: RunItem[]
  issue_count: number
}

export interface ReportPayload {
  report_no: string
  generated_at: string
  dataset: Record<string, string | number>
  batch: RuleRun
  rules: Array<RunItem & { params: Record<string, unknown>; param_summary: string }>
  quantiles: Array<Record<string, string | number | null>>
  violation_samples: Array<Record<string, string | number | null>>
  summary: Record<string, number>
}

export interface QuotaSnapshotState {
  quota: number
  used: number
  remaining: number
}

export interface RunLockState {
  locked: boolean
  dataset_id: number | null
}
