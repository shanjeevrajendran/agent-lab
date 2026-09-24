"""Toy tools the agent can call. Each takes a string and returns a string."""
import ast
import operator

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}

# Synthetic facts only.
_FACTS = {
    "capital of zorland": "Zorvik",
    "founder of acme": "Jane Doe",
    "population of zorvik": "1200000",
}


def _eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
    raise ValueError("unsupported expression")


def calculator(expression: str) -> str:
    """Safely evaluate + - * / arithmetic, e.g. '17 * 3'."""
    try:
        return str(_eval(ast.parse(expression, mode="eval").body))
    except (ValueError, SyntaxError, ZeroDivisionError) as e:
        return f"error: {e}"


def lookup(query: str) -> str:
    """Look up a fact in the synthetic table."""
    return _FACTS.get(query.strip().lower(), "not found")


TOOLS = {"calculator": calculator, "lookup": lookup}
