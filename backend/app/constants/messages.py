"""User-facing copy shared by API responses, audit payloads, worker logs and the
report export. One edit here changes the API text, the audit row and the worker
log at the same time.
"""
from app.constants.severity import SEVERITY_LABELS
from app.constants.column_type import ColumnType

API_MESSAGES = {
    "LOGIN_OK": "登录成功",
    "LOGIN_BAD_CREDENTIALS": "邮箱或密码不正确",
    "UPLOAD_OK": "数据集已上传，剖析任务已入队",
    "PROFILE_ENQUEUED": "剖析任务已入队",
    "PROFILE_NOT_READY": "该数据集尚未完成剖析，请先执行剖析",
    "RULE_SAVED": "规则已保存，已记入审计",
    "RULE_DELETED": "规则已删除",
    "RUN_ENQUEUED": "批次已入队，正在逐条执行",
    "ISSUE_UPDATED": "问题单已更新",
    "REPORT_READY": "报告单已生成",
}

AUDIT_ACTIONS = {
    "DATASET_UPLOAD": "上传数据集",
    "DATASET_DELETE": "删除数据集",
    "PROFILE_RECOMPUTE": "重算剖析",
    "RULE_CREATE": "新建规则",
    "RULE_UPDATE": "修改规则",
    "RULE_TOGGLE": "启停规则",
    "RULE_DELETE": "删除规则",
    "RULE_BULK_RUN": "批量执行规则",
    "ISSUE_ASSIGN": "指派问题单",
    "ISSUE_STATUS": "流转问题单",
}

TASK_FAILURE_MESSAGES = {
    "PROFILE_FAILED": "剖析任务失败：{reason}",
    "RUN_FAILED": "规则执行失败：{reason}",
    "RECHECK_FAILED": "复检任务失败：{reason}",
}

TEXT_LABELS = {
    "DATASET_INDEX": "标本索引",
    "PROFILE_REPORT": "检验报告单",
    "RULE_BUILDER": "规则构建器",
    "RUN_LEDGER": "执行台账",
    "ISSUE_BOARD": "问题分诊板",
}

COLUMN_TYPE_LABELS = {
    ColumnType.INTEGER.value: "整数",
    ColumnType.DECIMAL.value: "小数",
    ColumnType.STRING.value: "文本",
    ColumnType.DATE.value: "日期",
    ColumnType.BOOLEAN.value: "布尔",
    ColumnType.UNKNOWN.value: "未知",
}

SEVERITY_TEXT = {k: f"{v}危" for k, v in SEVERITY_LABELS.items()}
