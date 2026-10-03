"""ReAct loop: the model reasons, picks a tool, we run it, repeat until done.

Model reply format:
    Action: tool_name[input]
    Final Answer: the answer
"""
import logging
import re
from dataclasses import dataclass

from adapters import PrivacyViolationError
from tools import TOOLS

log = logging.getLogger("agent-lab")

_ACTION = re.compile(r"Action:\s*(\w+)\[(.*)\]", re.DOTALL)
_FINAL = re.compile(r"Final Answer:\s*(.*)", re.DOTALL)

# Tuned against qwen3.5:27b (see live_check.py). Keep it short: the router counts it toward
# prompt length, so every extra character pushes more requests over the cloud threshold.
SYSTEM_PROMPT = (
    "Reply with ONE line: `Action: tool[input]` or `Final Answer: X`, where X is only the "
    "answer, no sentence. Tools: calculator[2 * 3], lookup[founder of X]. "
    "Look facts up; don't guess."
)


@dataclass
class AgentResult:
    answer: str
    steps: int
    cost_usd: float
    latency_s: float
    blocked: bool = False  # True if a privacy lock stopped the request


def run_agent(model, question: str, sensitivity=None, max_steps: int = 5) -> AgentResult:
    """`model` is anything with generate(messages, sensitivity) -> Reply (the router).

    `sensitivity` labels the request (see PRIVACY.md); missing means local-only.
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    cost = latency = 0.0

    for step in range(1, max_steps + 1):
        try:
            reply = model.generate(messages, sensitivity)
        except PrivacyViolationError as e:
            # Fail closed: stop the request, log loudly, report a clean failure.
            log.error("PRIVACY BLOCK (step %d): %s", step, e)
            return AgentResult("(blocked by privacy policy)", step, cost, latency, blocked=True)
        cost += reply.cost_usd
        latency += reply.latency_s
        messages.append({"role": "assistant", "content": reply.text})

        if m := _FINAL.search(reply.text):
            return AgentResult(m.group(1).strip(), step, cost, latency)

        if m := _ACTION.search(reply.text):
            name, arg = m.group(1), m.group(2)
            tool = TOOLS.get(name)
            obs = tool(arg) if tool else f"error: unknown tool '{name}'"
        else:
            obs = "error: reply must contain 'Action: tool[input]' or 'Final Answer: ...'"
        messages.append({"role": "user", "content": f"Observation: {obs}"})

    return AgentResult("(no answer: step limit reached)", max_steps, cost, latency)
