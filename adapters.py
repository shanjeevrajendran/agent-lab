"""Adapters: one shared shape for talking to any model.

LocalAdapter and CloudAdapter are stubs. They return scripted replies and report
made-up cost/latency, so the whole project runs with no keys or installs.
OllamaAdapter talks to a real model served by Ollama on this machine.
See PRIVACY.md for what each Sensitivity level means.
"""
import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from enum import Enum


class Sensitivity(str, Enum):
    LOCAL_ONLY = "local_only"
    CLOUD_SAFE = "cloud_safe"
    PUBLIC = "public"

    @classmethod
    def parse(cls, value) -> "Sensitivity":
        """Fail closed: anything missing or unrecognised is LOCAL_ONLY."""
        try:
            return cls(value)
        except ValueError:
            return cls.LOCAL_ONLY


class PrivacyViolationError(PermissionError):
    """Raised by an adapter's lock when it is sent data it may not receive."""


@dataclass
class Reply:
    text: str
    cost_usd: float
    latency_s: float


class Adapter:
    name = "base"
    allowed: frozenset = frozenset()  # sensitivity levels this adapter may see

    # Deliberately not named `generate`: only Router.generate is meant for agents to call, so
    # handing a raw adapter to run_agent fails loudly. See check_router_bypass.py.
    def complete(self, messages: list[dict], sensitivity=None) -> Reply:
        raise NotImplementedError

    def _check_allowed(self, sensitivity) -> None:
        """The adapter's own privacy lock, applied underneath the router."""
        level = Sensitivity.parse(sensitivity)
        if level not in self.allowed:
            raise PrivacyViolationError(f"{self.name} adapter may not receive {level.value} data")


class _ScriptedAdapter(Adapter):
    """Returns the next scripted reply each call (repeats the last one)."""

    cost_usd = 0.0
    latency_s = 0.0

    def __init__(self, script: list[str] | None = None):
        self.script = script or ["Final Answer: (stub reply)"]
        self._i = 0
        self.calls = 0  # invocation attempts, including ones that get blocked

    def complete(self, messages: list[dict], sensitivity=None) -> Reply:
        self.calls += 1
        self._check_allowed(sensitivity)
        text = self.script[min(self._i, len(self.script) - 1)]
        self._i += 1
        return Reply(text, self.cost_usd, self.latency_s)


class LocalAdapter(_ScriptedAdapter):
    """Stands in for a model running on your machine: free and fast."""

    name = "local"
    allowed = frozenset(Sensitivity)
    cost_usd = 0.0
    latency_s = 0.05


class CloudAdapter(_ScriptedAdapter):
    """Stands in for a hosted API: costs money and is slower."""

    name = "cloud"
    allowed = frozenset({Sensitivity.CLOUD_SAFE, Sensitivity.PUBLIC})
    cost_usd = 0.002
    latency_s = 0.4


class OllamaAdapter(Adapter):
    """A real model running on this machine via Ollama: free, but real latency."""

    name = "local"
    allowed = frozenset(Sensitivity)

    # The model must stop after each Action and wait for the real Observation.
    STOP = ("Observation:",)

    def __init__(self, model: str = "qwen3.5:27b", url: str = "http://localhost:11434",
                 timeout_s: float = 300, max_tokens: int = 256):
        self.model = model
        self.url = url.rstrip("/")
        self.timeout_s = timeout_s
        self.max_tokens = max_tokens  # caps rambling replies, which otherwise hit the timeout

    @classmethod
    def from_env(cls, **kwargs) -> "OllamaAdapter":
        """Build from LOCAL_MODEL / LOCAL_MODEL_URL (environment, then .env, then defaults)."""
        from config import setting
        return cls(model=setting("LOCAL_MODEL"), url=setting("LOCAL_MODEL_URL"), **kwargs)

    def complete(self, messages: list[dict], sensitivity=None) -> Reply:
        self._check_allowed(sensitivity)
        body = json.dumps({
            "model": self.model,
            "messages": messages,
            "stream": False,
            "think": False,
            "options": {"temperature": 0, "num_predict": self.max_tokens,
                        "stop": list(self.STOP)},
        }).encode()
        req = urllib.request.Request(f"{self.url}/api/chat", data=body,
                                     headers={"Content-Type": "application/json"})
        start = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                data = json.load(resp)
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:300]
            raise RuntimeError(f"Ollama HTTP {e.code} for model {self.model!r}: {detail}") from e
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            raise RuntimeError(f"Ollama not reachable at {self.url} ({e}). "
                               "Is it running? Try `ollama serve`.") from e
        return Reply(data["message"]["content"], 0.0, time.monotonic() - start)
