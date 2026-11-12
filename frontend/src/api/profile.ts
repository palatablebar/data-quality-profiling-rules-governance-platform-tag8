import http from './http'
import type { ColumnProfile, ProfilePayload, RuleSuggestion } from '../types/profile'

export async function fetchProfile(datasetId: number): Promise<ProfilePayload> {
  const { data } = await http.get<ProfilePayload>(`/datasets/${datasetId}/profile`)
  return data
}

export async function recomputeProfile(datasetId: number): Promise<{ run_id: number; status: string }> {
  const { data } = await http.post(`/datasets/${datasetId}/profile`)
  return data
}

export async function fetchColumns(datasetId: number): Promise<{ columns: ColumnProfile[] }> {
  const { data } = await http.get(`/datasets/${datasetId}/columns`)
  return data
}

export async function fetchRecommendations(datasetId: number, limit = 5): Promise<{ items: RuleSuggestion[] }> {
  const { data } = await http.get(`/datasets/${datasetId}/recommendations`, { params: { limit } })
  return data
}
