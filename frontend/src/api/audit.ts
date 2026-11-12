import http from './http'
import type { AuditEntry } from '../types/audit'

export async function fetchRecentAudit(limit = 10): Promise<{ items: AuditEntry[] }> {
  const { data } = await http.get('/audit/recent', { params: { limit } })
  return data
}
