export interface Issue {
  id: number
  rule_run_id: number
  rule_id: number | null
  rule_name: string | null
  rule_type: string | null
  severity: string
  severity_label: string
  column_name: string
  row_index: number
  observed_value: string | null
  expected_expr: string | null
  status: string
  assignee_id: number | null
  assignee_name: string | null
  note: string | null
  dataset_name: string | null
  report_no: string | null
  created_at: string | null
  repro_snippet: string
}

export interface IssueSummary {
  total: number
  by_severity: Record<string, number>
  by_status: Record<string, number>
  dataset_id: number | null
}
