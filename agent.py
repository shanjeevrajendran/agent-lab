"""ReAct loop: the model reasons, picks a tool, we run it, repeat until done.

Model reply format:
    Action: tool_name[input]
    Final Answer: the answer
"""
import re
from dataclasses import dataclass

from tools import TOOLS

_ACTION = re.compile(r"Action:\s*(\w+)\[(.*)\]", re.DOTALL)
_FINAL = re.compile(r"Final Answer:\s*(.*)", re.DOTALL)

SYSTEM_PROMPT = (
    "Answer the question. To use a tool, reply `Action: tool_name[input]`. "
    f"Tools: {', '.join(TOOLS)}. When done, reply `Final Answer: ...`."
)


@dataclass
class AgentResult:
    answer: str
    steps: int
    cost_usd: float
    latency_s: float


def run_agent(model, question: str, sensitivity=None, max_steps: int = 5) -> AgentResult:
    """`model` is anything with generate(messages, sensitivity) -> Reply (adapter or router).

    `sensitivity` labels the request (see PRIVACY.md); missing means local-only.
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    cost = latency = 0.0

    for step in range(1, max_steps + 1):
        reply = model.generate(messages, sensitivity)
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
