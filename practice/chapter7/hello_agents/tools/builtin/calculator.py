import ast
import operator
import math
from ..base import BaseTool


def calculate(expression: str) -> str:
    if not expression.strip():
        return "计算表达式不能为空"
    ops = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
    }
    funcs = {"sqrt": math.sqrt, "pi": math.pi}
    try:
        node = ast.parse(expression, mode="eval")
        result = _eval(node.body, ops, funcs)
        return str(result)
    except Exception:
        return "计算失败，请检查表达式格式"


def _eval(node, ops, funcs):
    if isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.BinOp):
        left = _eval(node.left, ops, funcs)
        right = _eval(node.right, ops, funcs)
        op = ops.get(type(node.op))
        if op:
            return op(left, right)
    elif isinstance(node, ast.Call):
        fn = funcs.get(node.func.id)
        if fn:
            args = [_eval(a, ops, funcs) for a in node.args]
            return fn(*args)
    elif isinstance(node, ast.Name):
        return funcs.get(node.id)
    raise ValueError("不支持的表达式")


class CalculatorTool(BaseTool):

    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return "数学计算工具，支持基本的四则运算(+,-,*,/)和sqrt函数"

    def run(self, params) -> str:
        if isinstance(params, dict):
            expression = params.get("expression", params.get("input", ""))
        else:
            expression = str(params)
        return calculate(expression)
