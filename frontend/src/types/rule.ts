import type { Severity } from '../constants/severity'
import type { RuleType } from '../constants/ruleType'

export interface QualityRule {
  id: number
  dataset_id: number
  name: string
  rule_type: RuleType | string
  rule_type_label: string
  column_name: string
  params: Record<string, unknown>
  param_summary: string
  severity: Severity | string
  severity_label: string
  is_active: boolean
  sample_limit: number
  created_by: number
  created_at: string | null
  updated_at: string | null
}

export interface RuleDraft {
  id?: number
  dataset_id: number | null
  name: string
  rule_type: string
  column_name: string
  severity: string
  is_active: boolean
  sample_limit: number
  min: string
  max: string
  pattern: string
  values: string
  target_dataset_id: string
  target_column: string
  expr: string
}
