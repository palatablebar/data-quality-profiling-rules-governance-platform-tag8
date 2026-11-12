import { defineStore } from 'pinia'
import { fetchProfile, recomputeProfile } from '../api/profile'
import type { ProfilePayload } from '../types/profile'

interface ProfileState {
  cache: Record<string, ProfilePayload>
  loading: boolean
  recomputing: boolean
  error: string
}

export const useProfileStore = defineStore('profile', {
  state: (): ProfileState => ({ cache: {}, loading: false, recomputing: false, error: '' }),
  actions: {
    key(datasetId: number, runId?: number | null) {
      return `${datasetId}:${runId ?? 'latest'}`
    },
    async load(datasetId: number, force = false) {
      this.loading = true
      this.error = ''
      try {
        const payload = await fetchProfile(datasetId)
        const key = this.key(datasetId, payload.run?.run_id ?? null)
        if (!force) this.cache[key] = payload
        this.cache[this.key(datasetId)] = payload
        return payload
      } catch (error) {
        this.error = (error as { message?: string }).message ?? '剖析结果加载失败'
        throw error
      } finally {
        this.loading = false
      }
    },
    async recompute(datasetId: number) {
      this.recomputing = true
      try {
        return await recomputeProfile(datasetId)
      } finally {
        this.recomputing = false
      }
    },
  },
})
