import { ColumnType, NUMERIC_COLUMN_TYPES } from '../constants/columnType'

export function isNumericType(type: string | null | undefined): boolean {
  return !!type && NUMERIC_COLUMN_TYPES.includes(type as ColumnType)
}

export function alignClass(type: string | null | undefined): string {
  return isNumericType(type) ? 'num' : ''
}

export function truncate(value: string | null | undefined, length = 36): string {
  if (value === null || value === undefined) return '-'
  return value.length > length ? `${value.slice(0, length)}…` : value
}

export function formatCell(value: string | null | undefined): string {
  if (value === null || value === undefined || value === '') return '∅'
  return value
}
