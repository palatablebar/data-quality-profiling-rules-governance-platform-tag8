import http from './http'
import type { ReportPayload, RuleRun, RunDetail } from '../types/run'
import type { ListResponse } from '../types/api'

export async function fetchRuns(params: { dataset_id?: number | null; kind?: string } = {}): Promise<ListResponse<RuleRun>> {
  const { data } = await http.get('/runs', {
    params: { ...(params.dataset_id ? { dataset_id: params.dataset_id } : {}), kind: params.kind ?? 'rules' },
  })
  return data
}

export async function fetchRunDetail(runId: number): Promise<RunDetail> {
  const { data } = await http.get<RunDetail>(`/runs/${runId}`)
  return data
}

export async function fetchReport(runId: number): Promise<ReportPayload> {
  const { data } = await http.get<ReportPayload>(`/runs/${runId}/report`)
  return data
}

export async function cancelRun(runId: number): Promise<RuleRun> {
  const { data } = await http.post<RuleRun>(`/runs/${runId}/cancel`)
  return data
}
