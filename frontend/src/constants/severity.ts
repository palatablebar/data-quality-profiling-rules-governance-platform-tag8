// Severity — mirror of backend/app/constants/severity.py
export enum Severity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical',
}

export const SEVERITY_LABELS: Record<string, string> = {
  [Severity.LOW]: '低',
  [Severity.MEDIUM]: '中',
  [Severity.HIGH]: '高',
  [Severity.CRITICAL]: '严重',
}

export const SEVERITY_ORDER: Record<string, number> = {
  [Severity.CRITICAL]: 0,
  [Severity.HIGH]: 1,
  [Severity.MEDIUM]: 2,
  [Severity.LOW]: 3,
}

export const SEVERITY_WEIGHT: Record<string, number> = {
  [Severity.LOW]: 1,
  [Severity.MEDIUM]: 2,
  [Severity.HIGH]: 3,
  [Severity.CRITICAL]: 4,
}

export const SEVERITY_LIST = [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW]
