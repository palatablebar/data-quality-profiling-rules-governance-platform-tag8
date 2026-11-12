export type AuditAction =
  | '上传数据集'
  | '删除数据集'
  | '重算剖析'
  | '新建规则'
  | '修改规则'
  | '启停规则'
  | '删除规则'
  | '批量执行规则'
  | '指派问题单'
  | '流转问题单'

export interface AuditEntry {
  id: number
  actor_id: number | null
  actor_name: string | null
  action: AuditAction | string
  entity_type: string
  entity_id: number | null
  before_json: Record<string, unknown> | null
  after_json: Record<string, unknown> | null
  ip: string | null
  created_at: string | null
}
