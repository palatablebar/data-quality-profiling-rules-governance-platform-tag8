import { defineStore } from 'pinia'
import { bulkRun, createRule, deleteRule, draftToPayload, fetchRules, toggleRule, updateRule } from '../api/rule'
import type { QualityRule, RuleDraft } from '../types/rule'
import type { RuleSuggestion } from '../types/profile'

interface RuleState {
  items: QualityRule[]
  loading: boolean
  saving: boolean
  running: boolean
  lastAuditNotice: string
  error: string
}

export const useRuleStore = defineStore('rule', {
  state: (): RuleState => ({
    items: [],
    loading: false,
    saving: false,
    running: false,
    lastAuditNotice: '',
    error: '',
  }),
  getters: {
    activeCount: (state): number => state.items.filter((rule) => rule.is_active).length,
  },
  actions: {
    async load(datasetId?: number | null) {
      this.loading = true
      this.error = ''
      try {
        const result = await fetchRules(datasetId ?? null)
        this.items = result.items
      } catch (error) {
        this.error = (error as { message?: string }).message ?? '规则加载失败'
      } finally {
        this.loading = false
      }
    },
    async save(draft: RuleDraft) {
      this.saving = true
      this.error = ''
      try {
        const payload = draftToPayload(draft)
        const saved = draft.id ? await updateRule(draft.id, payload) : await createRule(payload)
        await this.load(payload.dataset_id)
        this.lastAuditNotice = '规则已保存，已记入审计'
        return saved
      } catch (error) {
        this.error = (error as { message?: string }).message ?? '规则保存失败'
        throw error
      } finally {
        this.saving = false
      }
    },
    async toggle(ruleId: number, isActive: boolean) {
      const rule = await toggleRule(ruleId, isActive)
      const index = this.items.findIndex((item) => item.id === ruleId)
      if (index >= 0) this.items[index] = rule
      this.lastAuditNotice = `规则已${isActive ? '启用' : '停用'}，已记入审计`
      return rule
    },
    async remove(ruleId: number, datasetId: number) {
      await deleteRule(ruleId)
      await this.load(datasetId)
      this.lastAuditNotice = '规则已删除，已记入审计'
    },
    async runAll(datasetId: number, ruleIds?: number[]) {
      this.running = true
      try {
        return await bulkRun(datasetId, ruleIds)
      } finally {
        this.running = false
      }
    },
    fromSuggestion(suggestion: RuleSuggestion, datasetId: number): RuleDraft {
      const params = suggestion.params as Record<string, unknown>
      return {
        dataset_id: datasetId,
        name: `${suggestion.column_name} · ${suggestion.rule_type}`,
        rule_type: suggestion.rule_type,
        column_name: suggestion.column_name,
        severity: suggestion.severity,
        is_active: true,
        sample_limit: 200,
        min: params.min === undefined ? '' : String(params.min),
        max: params.max === undefined ? '' : String(params.max),
        pattern: params.pattern === undefined ? '' : String(params.pattern),
        values: Array.isArray(params.values) ? (params.values as string[]).join(', ') : '',
        target_dataset_id: '',
        target_column: '',
        expr: '',
      }
    },
  },
})
