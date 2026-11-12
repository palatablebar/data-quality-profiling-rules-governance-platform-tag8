import http from './http'
import type { Issue, IssueSummary } from '../types/issue'
import type { Page } from '../types/api'

export interface IssueFilters {
  dataset_id?: number | null
  severity?: string | null
  status?: string | null
  rule_id?: number | null
  assignee_id?: number | null
  page?: number
  page_size?: number
}

export async function fetchIssues(filters: IssueFilters = {}): Promise<Page<Issue>> {
  const params: Record<string, unknown> = {}
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== '') params[key] = value
  })
  const { data } = await http.get<Page<Issue>>('/issues', { params })
  return data
}

export async function fetchIssueSummary(datasetId?: number | null): Promise<IssueSummary> {
  const { data } = await http.get<IssueSummary>('/issues/summary', {
    params: datasetId ? { dataset_id: datasetId } : {},
  })
  return data
}

export async function updateIssue(
  issueId: number,
  payload: { status?: string; assignee_id?: number | null; note?: string },
): Promise<Issue> {
  const { data } = await http.patch<Issue>(`/issues/${issueId}`, payload)
  return data
}

export async function bulkAssign(payload: {
  issue_ids: number[]
  assignee_id?: number | null
  status?: string | null
}): Promise<{ updated: number }> {
  const { data } = await http.post('/issues/bulk-assign', payload)
  return data
}
