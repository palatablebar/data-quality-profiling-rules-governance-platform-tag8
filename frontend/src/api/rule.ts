import http from './http'
import type { QualityRule, RuleDraft } from '../types/rule'

export interface RulePayload {
  dataset_id: number
  name: string
  rule_type: string
  column_name: string
  params: Record<string, unknown>
  severity: string
  is_active: boolean
  sample_limit: number
}

export async function fetchRules(datasetId?: number | null): Promise<{ items: QualityRule[]; total: number }> {
  const { data } = await http.get('/rules', { params: datasetId ? { dataset_id: datasetId } : {} })
  return data
}

export async function createRule(payload: RulePayload): Promise<QualityRule> {
  const { data } = await http.post<QualityRule>('/rules', payload)
  return data
}

export async function updateRule(ruleId: number, payload: Partial<RulePayload>): Promise<QualityRule> {
  const { data } = await http.patch<QualityRule>(`/rules/${ruleId}`, payload)
  return data
}

export async function toggleRule(ruleId: number, isActive: boolean): Promise<QualityRule> {
  const { data } = await http.post<QualityRule>(`/rules/${ruleId}/toggle`, null, {
    params: { is_active: isActive },
  })
  return data
}

export async function deleteRule(ruleId: number): Promise<{ deleted: boolean }> {
  const { data } = await http.delete(`/rules/${ruleId}`)
  return data
}

export async function bulkRun(datasetId: number, ruleIds?: number[]): Promise<{ run_id: number; status: string }> {
  const { data } = await http.post('/runs', { dataset_id: datasetId, rule_ids: ruleIds ?? null })
  return data
}

export function draftToPayload(draft: RuleDraft): RulePayload {
  const params: Record<string, unknown> = {}
  if (draft.rule_type === 'range') {
    params.min = draft.min === '' ? null : Number(draft.min)
    params.max = draft.max === '' ? null : Number(draft.max)
  } else if (draft.rule_type === 'regex') {
    params.pattern = draft.pattern
  } else if (draft.rule_type === 'enum_set') {
    params.values = draft.values
      .split(/[,，\s]+/)
      .map((item) => item.trim())
      .filter(Boolean)
  } else if (draft.rule_type === 'referential') {
    params.target_dataset_id = draft.target_dataset_id === '' ? null : Number(draft.target_dataset_id)
    params.target_column = draft.target_column
  } else if (draft.rule_type === 'expression') {
    params.expr = draft.expr
  }
  return {
    dataset_id: Number(draft.dataset_id),
    name: draft.name,
    rule_type: draft.rule_type,
    column_name: draft.column_name,
    params,
    severity: draft.severity,
    is_active: draft.is_active,
    sample_limit: draft.sample_limit,
  }
}
