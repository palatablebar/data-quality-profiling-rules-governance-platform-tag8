"""Central error-code catalogue + the AppError exception.

QUAL-2001 .. QUAL-2014 are referenced by services, controllers, tasks and by
frontend/src/constants/errorCodes.ts. Services raise AppError; controllers add
context (e.g. ``QualityRule[id=31] column=order_date``); error_handler.py turns
it into a uniform envelope.
"""
from enum import Enum


class ErrorCode(str, Enum):
    DATASET_NOT_FOUND = "QUAL-2001"
    FORMAT_UNSUPPORTED = "QUAL-2002"
    ENCODING_ERROR = "QUAL-2003"
    DUPLICATE_COLUMN = "QUAL-2004"
    ROW_LIMIT_EXCEEDED = "QUAL-2005"
    PROFILE_NOT_READY = "QUAL-2006"
    RULE_PARAMS_INVALID = "QUAL-2007"
    RULE_TYPE_MISMATCH = "QUAL-2008"
    EXPRESSION_SYNTAX = "QUAL-2009"
    REFERENTIAL_TARGET_MISSING = "QUAL-2010"
    RUN_LOCKED = "QUAL-2011"
    QUOTA_EXHAUSTED = "QUAL-2012"
    RATE_LIMITED = "QUAL-2013"
    ISSUE_CLOSED = "QUAL-2014"
    # auth-layer additions (not part of the data-quality catalogue)
    FORBIDDEN = "QUAL-2015"
    UNAUTHORIZED = "QUAL-2016"


ERROR_MESSAGES = {
    ErrorCode.DATASET_NOT_FOUND: "数据集不存在或已删除",
    ErrorCode.FORMAT_UNSUPPORTED: "文件格式不受支持",
    ErrorCode.ENCODING_ERROR: "文件编码不是 UTF-8",
    ErrorCode.DUPLICATE_COLUMN: "表头存在重复列名",
    ErrorCode.ROW_LIMIT_EXCEEDED: "数据行数超过上限",
    ErrorCode.PROFILE_NOT_READY: "该数据集尚未完成剖析",
    ErrorCode.RULE_PARAMS_INVALID: "规则参数非法",
    ErrorCode.RULE_TYPE_MISMATCH: "规则类型与列类型不匹配",
    ErrorCode.EXPRESSION_SYNTAX: "表达式语法错误",
    ErrorCode.REFERENTIAL_TARGET_MISSING: "引用规则的目标数据集缺失",
    ErrorCode.RUN_LOCKED: "该数据集已有批次在执行",
    ErrorCode.QUOTA_EXHAUSTED: "今日扫描配额已用尽",
    ErrorCode.RATE_LIMITED: "请求过于频繁",
    ErrorCode.ISSUE_CLOSED: "问题单已关闭，无法再流转",
    ErrorCode.FORBIDDEN: "当前角色无权执行该操作",
    ErrorCode.UNAUTHORIZED: "未登录或登录已过期",
}

ERROR_STATUS = {
    ErrorCode.DATASET_NOT_FOUND: 404,
    ErrorCode.FORMAT_UNSUPPORTED: 400,
    ErrorCode.ENCODING_ERROR: 400,
    ErrorCode.DUPLICATE_COLUMN: 400,
    ErrorCode.ROW_LIMIT_EXCEEDED: 400,
    ErrorCode.PROFILE_NOT_READY: 409,
    ErrorCode.RULE_PARAMS_INVALID: 400,
    ErrorCode.RULE_TYPE_MISMATCH: 400,
    ErrorCode.EXPRESSION_SYNTAX: 400,
    ErrorCode.REFERENTIAL_TARGET_MISSING: 400,
    ErrorCode.RUN_LOCKED: 409,
    ErrorCode.QUOTA_EXHAUSTED: 429,
    ErrorCode.RATE_LIMITED: 429,
    ErrorCode.ISSUE_CLOSED: 409,
    ErrorCode.FORBIDDEN: 403,
    ErrorCode.UNAUTHORIZED: 401,
}


class AppError(Exception):
    def __init__(self, code, message: str | None = None, detail=None, context: str | None = None, status_code: int | None = None):
        self.code = code.value if isinstance(code, ErrorCode) else str(code)
        try:
            enum_code = ErrorCode(self.code)
        except ValueError:
            enum_code = None
        self.message = message or (ERROR_MESSAGES.get(enum_code, "请求处理失败") if enum_code else "请求处理失败")
        if context:
            self.message = f"{self.message}（{context}）"
        self.detail = detail
        self.status_code = status_code or (ERROR_STATUS.get(enum_code, 400) if enum_code else 400)
        super().__init__(self.message)
