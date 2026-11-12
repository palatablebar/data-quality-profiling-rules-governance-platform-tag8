export interface TopValue {
  value: string
  count: number
}

export interface PercentilePositions {
  p50: number | null
  p95: number | null
}

export interface ColumnProfile {
  id: number
  dataset_id: number
  run_id: number | null
  column_name: string
  ordinal: number
  inferred_type: string
  type_label: string
  null_rate: number
  null_rate_display: string
  distinct_count: number
  distinct_display: string
  min_value: string | null
  max_value: string | null
  p50: number | null
  p95: number | null
  p50_display: string
  p95_display: string
  top_values: TopValue[]
  pattern_summary: string | null
  outlier_count: number
  percentile_positions: PercentilePositions
  is_numeric: boolean
  created_at: string | null
}

export interface ProfilePayload {
  dataset: {
    id: number
    name: string
    source_format: string
    row_count: number
    column_count: number
    checksum: string
    status: string
    uploaded_at: string | null
  }
  run: {
    run_id: number
    status: string
    started_at: string | null
    finished_at: string | null
    duration_ms: number
    rows_scanned: number
  } | null
  columns: ColumnProfile[]
  recommendations: RuleSuggestion[]
}

export interface RuleSuggestion {
  rule_type: string
  column_name: string
  params: Record<string, unknown>
  severity: string
  reason: string
}
