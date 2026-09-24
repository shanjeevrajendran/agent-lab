"""Fail if anything calls `.generate(` outside the files allowed to.

Only router.py (calls the adapters) and agent.py (calls whatever model it was given,
normally a Router) may call generate. Any other caller would bypass the router's
privacy check.

Limit: this cannot catch a raw adapter being passed to run_agent as the model.
"""
import ast
import sys
from pathlib import Path

ALLOWED = {"router.py", "agent.py"}


def violations(root: Path) -> list[str]:
    found = []
    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root)
        if any(part.startswith(".") or part == "__pycache__" for part in rel.parts):
            continue
        if rel.as_posix() in ALLOWED:
            continue
        for node in ast.walk(ast.parse(path.read_text(), filename=str(path))):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "generate"):
                found.append(f"{rel}:{node.lineno}: .generate() called outside router.py/agent.py")
    return found


def main() -> int:
    found = violations(Path(__file__).parent)
    for line in found:
        print(line)
    print("router-bypass check:", "FAILED" if found else "ok")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
