// ColumnType — mirror of backend/app/constants/column_type.py
export enum ColumnType {
  INTEGER = 'integer',
  DECIMAL = 'decimal',
  STRING = 'string',
  DATE = 'date',
  BOOLEAN = 'boolean',
  UNKNOWN = 'unknown',
}

export const COLUMN_TYPE_LABELS: Record<string, string> = {
  [ColumnType.INTEGER]: '整数',
  [ColumnType.DECIMAL]: '小数',
  [ColumnType.STRING]: '文本',
  [ColumnType.DATE]: '日期',
  [ColumnType.BOOLEAN]: '布尔',
  [ColumnType.UNKNOWN]: '未知',
}

export const NUMERIC_COLUMN_TYPES = [ColumnType.INTEGER, ColumnType.DECIMAL]
