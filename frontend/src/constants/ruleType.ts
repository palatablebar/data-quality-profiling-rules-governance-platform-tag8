// RuleType — mirror of backend/app/constants/rule_type.py
export enum RuleType {
  NOT_NULL = 'not_null',
  UNIQUE = 'unique',
  RANGE = 'range',
  REGEX = 'regex',
  ENUM_SET = 'enum_set',
  REFERENTIAL = 'referential',
  EXPRESSION = 'expression',
}

export const RULE_TYPE_LABELS: Record<string, string> = {
  [RuleType.NOT_NULL]: '非空',
  [RuleType.UNIQUE]: '唯一',
  [RuleType.RANGE]: '范围',
  [RuleType.REGEX]: '正则',
  [RuleType.ENUM_SET]: '枚举',
  [RuleType.REFERENTIAL]: '引用',
  [RuleType.EXPRESSION]: '表达式',
}

export const RULE_TYPE_HINTS: Record<string, string> = {
  [RuleType.NOT_NULL]: '列值为空即违规',
  [RuleType.UNIQUE]: '同一值出现两次及以上即违规',
  [RuleType.RANGE]: '数值必须落在 min 与 max 之间',
  [RuleType.REGEX]: '整值匹配，例如 \\d{18}',
  [RuleType.ENUM_SET]: '取值必须在枚举集合内',
  [RuleType.REFERENTIAL]: '取值必须存在于目标数据集的目标列',
  [RuleType.EXPRESSION]: '白名单表达式，例如 balance > 0 and status in ["A","I"]',
}

export const RULE_TYPE_LIST = Object.values(RuleType)
