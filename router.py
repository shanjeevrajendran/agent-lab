"""Router: privacy first, then cost/latency. Logs every decision."""
from adapters import Adapter, Reply, Sensitivity

# Prompt length is a provisional stand-in for task difficulty. When it is replaced,
# re-check the long cases in cases.json.
DEFAULT_LONG_PROMPT_CHARS = 200
PRIVACY_REASON = "privacy: local-only"


class Router:
    def __init__(self, local: Adapter, cloud: Adapter,
                 long_prompt_chars: int = DEFAULT_LONG_PROMPT_CHARS):
        self.local = local
        self.cloud = cloud
        self.long_prompt_chars = long_prompt_chars
        self.log: list[dict] = []

    def choose(self, messages: list[dict], sensitivity=None) -> tuple[Adapter, str]:
        # Check 1: privacy. LOCAL_ONLY (and anything unknown) never leaves the machine.
        if Sensitivity.parse(sensitivity) is Sensitivity.LOCAL_ONLY:
            return self.local, PRIVACY_REASON
        # Check 2: cost/latency. Prompt length stands in for task difficulty.
        size = sum(len(m["content"]) for m in messages)
        if size < self.long_prompt_chars:
            return self.local, "cost: short prompt"
        return self.cloud, "quality: long prompt"

    def generate(self, messages: list[dict], sensitivity=None) -> Reply:
        adapter, reason = self.choose(messages, sensitivity)
        reply = adapter.generate(messages, sensitivity)
        self.log.append({
            "adapter": adapter.name,
            "reason": reason,
            "sensitivity": Sensitivity.parse(sensitivity).value,
            "cost_usd": reply.cost_usd,
            "latency_s": reply.latency_s,
        })
        return reply
