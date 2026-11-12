import http from './http'
import type { Dataset } from '../types/dataset'
import type { ListResponse } from '../types/api'
import type { QuotaSnapshot } from '../types/user'

export async function fetchDatasets(): Promise<ListResponse<Dataset> & { quota: QuotaSnapshot }> {
  const { data } = await http.get('/datasets')
  return data
}

export async function uploadDataset(file: File): Promise<{ dataset: Dataset; profile_run_id: number }> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await http.post('/datasets/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function deleteDataset(datasetId: number): Promise<{ deleted: boolean }> {
  const { data } = await http.delete(`/datasets/${datasetId}`)
  return data
}

export async function fetchDataset(datasetId: number): Promise<Dataset> {
  const { data } = await http.get<Dataset>(`/datasets/${datasetId}`)
  return data
}
