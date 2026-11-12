import { Severity } from '../constants/severity'

export interface SeverityTone {
  color: string
  label: string
  shape: 'tick' | 'bar' | 'double-bar' | 'block'
}

// Returns CSS variable references only — components must not hardcode colours.
export function severityTone(severity: string): SeverityTone {
  switch (severity) {
    case Severity.CRITICAL:
      return { color: 'var(--alert-deep)', label: '严重', shape: 'block' }
    case Severity.HIGH:
      return { color: 'var(--alert)', label: '高', shape: 'double-bar' }
    case Severity.MEDIUM:
      return { color: 'var(--ink-soft)', label: '中', shape: 'bar' }
    default:
      return { color: 'var(--low)', label: '低', shape: 'tick' }
  }
}
