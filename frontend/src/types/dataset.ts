export interface ProfileRunRef {
  run_id: number
  status: string
  started_at: string | null
  finished_at: string | null
  duration_ms: number
  rows_scanned: number
}

export interface Dataset {
  id: number
  owner_id: number
  name: string
  source_format: string
  row_count: number
  column_count: number
  file_size: number
  checksum: string
  status: string
  uploaded_at: string | null
  rule_count: number
  open_issues: number
  row_count_display: string
  last_profile: ProfileRunRef | null
}
