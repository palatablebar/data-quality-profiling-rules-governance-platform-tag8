import { computed, ref } from 'vue'
import { useProfileStore } from '../stores/profileStore'
import type { ProfilePayload } from '../types/profile'

export function useProfileQuery() {
  const store = useProfileStore()
  const payload = ref<ProfilePayload | null>(null)
  const error = ref('')
  const loading = computed(() => store.loading)
  const recomputing = computed(() => store.recomputing)

  async function load(datasetId: number, force = false) {
    error.value = ''
    try {
      payload.value = await store.load(datasetId, force)
      return payload.value
    } catch (err) {
      error.value = (err as { message?: string }).message ?? '剖析结果加载失败'
      return null
    }
  }

  async function recompute(datasetId: number) {
    error.value = ''
    const result = await store.recompute(datasetId)
    await load(datasetId, true)
    return result
  }

  return { payload, loading, recomputing, error, load, recompute }
}
