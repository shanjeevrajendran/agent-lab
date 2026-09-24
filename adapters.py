"""Adapters: one shared shape for talking to any model.

Both adapters here are stubs. They return scripted replies and report
made-up cost/latency, so the whole project runs with no keys or installs.
See PRIVACY.md for what each Sensitivity level means.
"""
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
        level = Sensitivity.parse(sensitivity)
        if level not in self.allowed:
            raise PrivacyViolationError(f"{self.name} adapter may not receive {level.value} data")
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
