import { defineStore } from 'pinia'
import { fetchRunDetail, fetchRuns } from '../api/run'
import type { QuotaSnapshot } from '../types/user'
import type { RuleRun, RunDetail } from '../types/run'

interface RunState {
  runs: RuleRun[]
  detail: RunDetail | null
  loading: boolean
  quota: QuotaSnapshot | null
  polling: boolean
  attempts: number
  error: string
}

export const useRunStore = defineStore('run', {
  state: (): RunState => ({
    runs: [],
    detail: null,
    loading: false,
    quota: null,
    polling: false,
    attempts: 0,
    error: '',
  }),
  getters: {
    quotaRemaining: (state): number => state.quota?.quota_remaining ?? 0,
    quotaTotal: (state): number => state.quota?.daily_scan_quota ?? 0,
  },
  actions: {
    setQuota(snapshot: QuotaSnapshot | null) {
      this.quota = snapshot
    },
    async loadRuns(datasetId?: number | null) {
      this.loading = true
      try {
        const result = await fetchRuns({ dataset_id: datasetId ?? null })
        this.runs = result.items
      } catch (error) {
        this.error = (error as { message?: string }).message ?? '批次加载失败'
      } finally {
        this.loading = false
      }
    },
    async loadDetail(runId: number) {
      this.detail = await fetchRunDetail(runId)
      return this.detail
    },
    async refreshDetail(runId: number) {
      try {
        const detail = await fetchRunDetail(runId)
        this.detail = detail
        const index = this.runs.findIndex((run) => run.id === detail.id)
        if (index >= 0) this.runs[index] = detail
        return detail
      } catch (error) {
        this.error = (error as { message?: string }).message ?? '批次详情加载失败'
        return null
      }
    },
  },
})
