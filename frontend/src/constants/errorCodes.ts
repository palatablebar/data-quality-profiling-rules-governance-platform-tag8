// Same catalogue as backend/app/constants/error_codes.py
export const ERROR_CODES: Record<string, { message: string; hint: string }> = {
  'QUAL-2001': { message: '数据集不存在或已删除', hint: '回到标本索引重新上传' },
  'QUAL-2002': { message: '文件格式不受支持', hint: '仅支持 .csv / .parquet / .jsonl / .xlsx' },
  'QUAL-2003': { message: '文件编码不是 UTF-8', hint: '转码：iconv -f GBK -t UTF-8 in.csv > out.csv' },
  'QUAL-2004': { message: '表头存在重复列名', hint: '把重复列改名后重新上传' },
  'QUAL-2005': { message: '数据行数超过上限', hint: '抽样后再上传（MAX_ROWS 可调）' },
  'QUAL-2006': { message: '该数据集尚未完成剖析', hint: '先点击「重算剖析」' },
  'QUAL-2007': { message: '规则参数非法', hint: '检查参数面板里的内联提示' },
  'QUAL-2008': { message: '规则类型与列类型不匹配', hint: 'range 只能用于数值列' },
  'QUAL-2009': { message: '表达式语法错误', hint: '按提示的字符位置修改表达式' },
  'QUAL-2010': { message: '引用数据集缺失', hint: '确认目标数据集仍在且启用' },
  'QUAL-2011': { message: '该数据集已有批次在执行', hint: '等上一批次结束后再执行' },
  'QUAL-2012': { message: '今日扫描配额已用尽', hint: '明天配额自动重置，或让管家扩容' },
  'QUAL-2013': { message: '请求过于频繁', hint: '稍后自动退避重试' },
  'QUAL-2014': { message: '问题单已关闭，无法再流转', hint: '先把状态改回 open' },
  'QUAL-2015': { message: '当前角色无权执行该操作', hint: '用管家或分析师账号登录' },
  'QUAL-2016': { message: '未登录或登录已过期', hint: '重新登录' },
}
