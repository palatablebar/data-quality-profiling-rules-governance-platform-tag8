import { computed, ref, watch } from 'vue'
import { emptyDraft, validateDraft } from '../utils/ruleSerialize'
import type { RuleDraft } from '../types/rule'
import type { RuleSuggestion } from '../types/profile'
import { useRuleStore } from '../stores/ruleStore'

export function useRuleDraft(initialDatasetId: number | null = null) {
  const store = useRuleStore()
  const draft = ref<RuleDraft>(emptyDraft(initialDatasetId))
  const dirty = ref(false)

  watch(
    draft,
    () => {
      dirty.value = true
    },
    { deep: true },
  )

  const issues = computed(() => validateDraft(draft.value))
  const valid = computed(() => issues.value.length === 0)

  function reset(datasetId = draft.value.dataset_id) {
    draft.value = emptyDraft(datasetId)
    dirty.value = false
  }

  function setDataset(datasetId: number | null) {
    draft.value.dataset_id = datasetId
  }

  function pickColumn(columnName: string) {
    draft.value.column_name = columnName
  }

  function applySuggestion(suggestion: RuleSuggestion, datasetId: number) {
    draft.value = store.fromSuggestion(suggestion, datasetId)
    dirty.value = true
  }

  function edit(rule: {
    id: number
    dataset_id: number
    name: string
    rule_type: string
    column_name: string
    severity: string
    is_active: boolean
    sample_limit: number
    params: Record<string, unknown>
  }) {
    const params = rule.params ?? {}
    draft.value = {
      id: rule.id,
      dataset_id: rule.dataset_id,
      name: rule.name,
      rule_type: rule.rule_type,
      column_name: rule.column_name,
      severity: rule.severity,
      is_active: rule.is_active,
      sample_limit: rule.sample_limit,
      min: params.min === undefined ? '' : String(params.min),
      max: params.max === undefined ? '' : String(params.max),
      pattern: params.pattern === undefined ? '' : String(params.pattern),
      values: Array.isArray(params.values) ? (params.values as string[]).join(', ') : '',
      target_dataset_id: params.target_dataset_id === undefined ? '' : String(params.target_dataset_id),
      target_column: params.target_column === undefined ? '' : String(params.target_column),
      expr: params.expr === undefined ? '' : String(params.expr),
    }
    dirty.value = false
  }

  async function save() {
    const saved = await store.save(draft.value)
    dirty.value = false
    return saved
  }

  return { draft, dirty, issues, valid, reset, setDataset, pickColumn, applySuggestion, edit, save }
}
