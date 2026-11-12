import { SEVERITY_WEIGHT } from '../constants/severity'

/** 0.0342 -> "3.42%" */
export function formatRate(value: number | null | undefined, digits = 2): string {
  if (value === null || value === undefined) return '-'
  return `${(Number(value) * 100).toFixed(digits)}%`
}

/** Weighted quality score (1 - weighted failure ratio), 0..1 */
export function weightedQuality(items: Array<{ severity: string; passed: boolean }>): number {
  let total = 0
  let ok = 0
  items.forEach((item) => {
    const weight = SEVERITY_WEIGHT[item.severity] ?? 1
    total += weight
    if (item.passed) ok += weight
  })
  return total === 0 ? 1 : ok / total
}

/** Map a percentile to a 0..1 position on the scale. */
export function axisPosition(value: number | null, min: number, max: number): number | null {
  if (value === null || Number.isNaN(value) || max <= min) return null
  return Math.min(1, Math.max(0, (value - min) / (max - min)))
}
