export type UserRole = 'steward' | 'analyst' | 'viewer'

export interface QuotaSnapshot {
  daily_scan_quota: number
  quota_used: number
  quota_remaining: number
  quota_used_date: string | null
  window_max: number
  window_seconds: number
}

export interface User {
  id: number
  email: string
  display_name: string
  role: UserRole
  daily_scan_quota: number
  quota_used: number
  quota_used_date: string | null
  created_at: string | null
  quota?: QuotaSnapshot
}

export const ROLE_LABELS: Record<UserRole, string> = {
  steward: '数据管家',
  analyst: '分析师',
  viewer: '审计',
}
