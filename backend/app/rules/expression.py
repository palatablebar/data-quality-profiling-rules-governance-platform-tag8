"""expression: whitelisted boolean expression evaluated per row.

Only these operators/functions are accepted:
    > >= < <= == != and or not in abs len
Attribute access, indexing, imports and every other call are rejected — the AST
is validated before a single row is evaluated. Syntax errors report the exact
character offset so the parameter panel can point at it.
"""
import ast

from app.constants.error_codes import AppError, ErrorCode
from app.constants.rule_type import RuleType
from app.rules.base import RuleContext, RuleResult

RULE_TYPE = RuleType.EXPRESSION.value
LABEL = "表达式"

ALLOWED_NODES = (
    ast.Expression,
    ast.BoolOp,
    ast.UnaryOp,
    ast.Compare,
    ast.BinOp,
    ast.Name,
    ast.Load,
    ast.Constant,
    ast.Call,
    ast.And,
    ast.Or,
    ast.Not,
    ast.In,
    ast.NotIn,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Mod,
    ast.USub,
    ast.UAdd,
)
ALLOWED_FUNCS = {"abs": abs, "len": len}
ALLOWED_BINOPS = {ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod}
MAX_LENGTH = 400


def validate_expression(expr: str, columns: list[str] | None = None) -> ast.Expression:
    expr = (expr or "").strip()
    if not expr:
        raise AppError(ErrorCode.RULE_PARAMS_INVALID, message="表达式不能为空")
    if len(expr) > MAX_LENGTH:
        raise AppError(ErrorCode.EXPRESSION_SYNTAX, detail={"offset": MAX_LENGTH, "reason": "表达式过长"})
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        position = exc.offset if exc.offset and exc.offset > 0 else len(expr) + 1
        raise AppError(
            ErrorCode.EXPRESSION_SYNTAX,
            message=f"表达式语法错误（第 {position} 个字符）",
            detail={"offset": position, "text": exc.text, "reason": exc.msg},
        ) from exc

    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            raise AppError(
                ErrorCode.EXPRESSION_SYNTAX,
                message=f"不允许属性访问（第 {node.col_offset + 1} 个字符）",
                detail={"offset": node.col_offset + 1},
            )
        if isinstance(node, ast.Subscript):
            raise AppError(
                ErrorCode.EXPRESSION_SYNTAX,
                message=f"不允许下标访问（第 {node.col_offset + 1} 个字符）",
                detail={"offset": node.col_offset + 1},
            )
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in ALLOWED_FUNCS:
                name = getattr(node.func, "id", "?")
                raise AppError(
                    ErrorCode.EXPRESSION_SYNTAX,
                    message=f"不允许调用函数 {name}（第 {node.col_offset + 1} 个字符）",
                    detail={"offset": node.col_offset + 1},
                )
        if isinstance(node, ast.Name) and columns is not None:
            if node.id not in columns and node.id not in ALLOWED_FUNCS:
                raise AppError(
                    ErrorCode.EXPRESSION_SYNTAX,
                    message=f"未知列名 {node.id}（第 {node.col_offset + 1} 个字符）",
                    detail={"offset": node.col_offset + 1, "columns": columns},
                )
        if isinstance(node, ast.BinOp) and type(node.op) not in ALLOWED_BINOPS:
            raise AppError(ErrorCode.EXPRESSION_SYNTAX, message="不允许该二元运算符")
        if not isinstance(node, ALLOWED_NODES) and not isinstance(node, ast.operator):
            raise AppError(
                ErrorCode.EXPRESSION_SYNTAX,
                message=f"表达式包含不允许的语法：{type(node).__name__}",
                detail={"offset": getattr(node, "col_offset", 0) + 1},
            )
        if isinstance(node, ast.Constant) and not isinstance(node.value, (int, float, str, bool, type(None))):
            raise AppError(ErrorCode.EXPRESSION_SYNTAX, message="表达式常量类型不受支持")
    return tree


def _coerce(value: str):
    text = (value or "").strip()
    if text == "":
        return None
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        return text


def check(ctx: RuleContext) -> RuleResult:
    expr = str((ctx.params or {}).get("expr") or "")
    tree = validate_expression(expr, list(ctx.df.columns))
    code = compile(tree, "<expression>", "eval")
    frame = ctx.df
    samples: list[tuple[int, str, str]] = []
    violated_rows: set[int] = set()
    violations = 0
    columns = list(frame.columns)
    rows = frame.itertuples(index=True, name=None)
    for row in rows:
        row_index = int(row[0])
        env = {}
        for position, column in enumerate(columns):
            env[column] = _coerce(row[position + 1])
        try:
            ok = eval(code, {"__builtins__": {}}, {**ALLOWED_FUNCS, **env})  # noqa: S307
        except Exception:
            ok = False
        if not ok:
            violations += 1
            if len(violated_rows) < 20000:
                violated_rows.add(row_index)
            if len(samples) < ctx.sample_limit:
                samples.append((row_index, expr, f"期望 {expr} 为真"))
    expected = f"期望 {expr} 为真"
    return RuleResult(
        violation_count=violations,
        samples=samples,
        expected=expected,
        violated_rows=violated_rows,
    )
