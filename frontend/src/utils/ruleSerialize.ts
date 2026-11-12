import { RuleType } from '../constants/ruleType'
import type { RuleDraft } from '../types/rule'

export interface DraftIssue {
  field: string
  message: string
  offset?: number
}

/** Structure validator mirroring backend rules/registry.validate_params. */
export function validateDraft(draft: RuleDraft): DraftIssue[] {
  const issues: DraftIssue[] = []
  if (!draft.dataset_id) issues.push({ field: 'dataset', message: '请先选择数据集' })
  if (!draft.name.trim()) issues.push({ field: 'name', message: '规则名不能为空' })
  if (!draft.column_name) issues.push({ field: 'column', message: '请选择要校验的列' })

  if (draft.rule_type === RuleType.RANGE) {
    const min = Number(draft.min)
    const max = Number(draft.max)
    if (draft.min === '' || Number.isNaN(min)) issues.push({ field: 'min', message: 'min 必须是数字' })
    if (draft.max === '' || Number.isNaN(max)) issues.push({ field: 'max', message: 'max 必须是数字' })
    if (!Number.isNaN(min) && !Number.isNaN(max) && min > max) {
      issues.push({ field: 'max', message: 'min 不能大于 max' })
    }
  } else if (draft.rule_type === RuleType.REGEX) {
    if (!draft.pattern) {
      issues.push({ field: 'pattern', message: '正则不能为空' })
    } else {
      try {
        new RegExp(draft.pattern)
      } catch (error) {
        const message = (error as Error).message
        const match = /<anonymous>:(\d+)/.exec(message)
        issues.push({
          field: 'pattern',
          message: `正则无法编译：${message}`,
          offset: match ? Number(match[1]) : undefined,
        })
      }
    }
  } else if (draft.rule_type === RuleType.ENUM_SET) {
    const values = draft.values.split(/[,，\s]+/).filter(Boolean)
    if (values.length === 0) issues.push({ field: 'values', message: '至少填写一个枚举值' })
  } else if (draft.rule_type === RuleType.REFERENTIAL) {
    if (!draft.target_dataset_id) issues.push({ field: 'target', message: '请选择目标数据集' })
    if (!draft.target_column) issues.push({ field: 'target', message: '请填写目标列名' })
  } else if (draft.rule_type === RuleType.EXPRESSION) {
    if (!draft.expr.trim()) issues.push({ field: 'expr', message: '表达式不能为空' })
    const forbidden = /[.[\]]|import|__|\bexec\(|\beval\(/
    const hit = forbidden.exec(draft.expr)
    if (hit) {
      issues.push({
        field: 'expr',
        message: '不允许属性访问、下标访问或危险调用',
        offset: hit.index + 1,
      })
    }
    const balanced = (draft.expr.match(/\(/g)?.length ?? 0) === (draft.expr.match(/\)/g)?.length ?? 0)
    if (!balanced) issues.push({ field: 'expr', message: '括号不匹配' })
  }
  return issues
}

export function emptyDraft(datasetId: number | null): RuleDraft {
  return {
    dataset_id: datasetId,
    name: '',
    rule_type: RuleType.NOT_NULL,
    column_name: '',
    severity: 'medium',
    is_active: true,
    sample_limit: 200,
    min: '',
    max: '',
    pattern: '',
    values: '',
    target_dataset_id: '',
    target_column: '',
    expr: '',
  }
}
