"""Fail if anything but router.py can reach an adapter, or fake the router's entry point.

Two rules, both enforced everywhere except router.py:
  1. No `.complete(` calls. `complete` is the adapters' entry point; only the router calls it.
  2. No `def generate`. `generate` is the router's public entry point, which agents call. A
     class defining its own `generate` could be handed to run_agent and skip the router.
Calling `.generate(` is fine (agent.py does): the only real `generate` is the router's.

The adapters' own lock (CloudAdapter refusing local_only data) still applies underneath.
"""
import ast
import sys
from pathlib import Path

ALLOWED = {"router.py"}


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
                    and node.func.attr == "complete"):
                found.append(f"{rel}:{node.lineno}: .complete() called outside router.py")
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "generate":
                found.append(f"{rel}:{node.lineno}: def generate outside router.py")
    return found


def main() -> int:
    found = violations(Path(__file__).parent)
    for line in found:
        print(line)
    print("router-bypass check:", "FAILED" if found else "ok")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
