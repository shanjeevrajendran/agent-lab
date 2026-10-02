"""Settings from .env (git-ignored), with real environment variables taking priority.

Stdlib only: a minimal KEY=VALUE reader, so the project still needs no installs.
"""
import os
from pathlib import Path

ENV_PATH = Path(__file__).parent / ".env"

DEFAULTS = {
    "LOCAL_MODEL_URL": "http://localhost:11434",
    "LOCAL_MODEL": "qwen3.5:27b",
}


def read_env_file(path: Path = ENV_PATH) -> dict[str, str]:
    """Parse KEY=VALUE lines; skip blanks and # comments; strip matching quotes."""
    values = {}
    if not path.exists():
        return values
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key] = value
    return values


def setting(key: str, path: Path = ENV_PATH) -> str | None:
    """Environment variable, else .env, else the built-in default."""
    if key in os.environ:
        return os.environ[key]
    return read_env_file(path).get(key, DEFAULTS.get(key))
