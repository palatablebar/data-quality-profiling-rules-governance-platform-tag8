import { defineStore } from 'pinia'
import { deleteDataset, fetchDatasets, uploadDataset } from '../api/dataset'
import type { Dataset } from '../types/dataset'
import { useRunStore } from './runStore'

interface DatasetState {
  items: Dataset[]
  loading: boolean
  uploading: boolean
  error: string
}

export const useDatasetStore = defineStore('dataset', {
  state: (): DatasetState => ({ items: [], loading: false, uploading: false, error: '' }),
  getters: {
    byId: (state) => (id: number): Dataset | undefined => state.items.find((item) => item.id === id),
  },
  actions: {
    async load() {
      this.loading = true
      this.error = ''
      try {
        const result = await fetchDatasets()
        this.items = result.items
        useRunStore().setQuota(result.quota ?? null)
      } catch (error) {
        this.error = (error as { message?: string }).message ?? '数据集加载失败'
      } finally {
        this.loading = false
      }
    },
    async upload(file: File) {
      this.uploading = true
      try {
        const result = await uploadDataset(file)
        await this.load()
        return result
      } finally {
        this.uploading = false
      }
    },
    async remove(datasetId: number) {
      await deleteDataset(datasetId)
      await this.load()
    },
  },
})
