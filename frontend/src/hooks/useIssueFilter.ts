import { reactive } from 'vue'
import { useIssueStore } from '../stores/issueStore'
import type { IssueFilterState } from '../stores/issueStore'

export function useIssueFilter(initial: Partial<IssueFilterState> = {}) {
  const store = useIssueStore()
  const filters = reactive<IssueFilterState>({
    dataset_id: initial.dataset_id ?? null,
    severity: initial.severity ?? null,
    status: initial.status ?? null,
    rule_id: initial.rule_id ?? null,
  })

  async function apply() {
    store.filters = { ...filters }
    await store.load()
  }

  function reset() {
    filters.dataset_id = null
    filters.severity = null
    filters.status = null
    filters.rule_id = null
    apply()
  }

  return { filters, apply, reset }
}
