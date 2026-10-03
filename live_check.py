"""Opt-in smoke test: four real questions through Router + OllamaAdapter.

Not part of evals or CI (CI has no Ollama). Needs Ollama running with LOCAL_MODEL pulled;
settings come from .env via config.py. Run: python3 live_check.py

Every question is labelled local_only, so the router must pick the local model for privacy
on every step. The cloud side is a stub that is never expected to be called.
"""
import logging
import sys

from adapters import CloudAdapter, OllamaAdapter
from agent import run_agent
from router import Router

QUESTIONS = [
    ("What is 17 * 3?", "51"),
    ("What is the capital of Zorland?", "Zorvik"),
    ("What is the population of Zorvik divided by 1000?", "1200"),
    ("Who founded Acme?", "Jane Doe"),
]


def main() -> int:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    local = OllamaAdapter.from_env()
    cloud = CloudAdapter(["Final Answer: (cloud stub: should never be called)"])
    print(f"model: {local.model} at {local.url}\n")

    matched = 0
    for question, expected in QUESTIONS:
        router = Router(local, cloud)
        try:
            result = run_agent(router, question, sensitivity="local_only")
        except RuntimeError as e:  # Ollama down or HTTP error
            print(f"error: {e}")
            return 2
        ok = result.answer.strip().rstrip(".") == expected
        matched += ok
        print(f"Q: {question}")
        print(f"A: {result.answer}   [{'match' if ok else f'expected {expected}'}]")
        print(f"   steps {result.steps} | {result.latency_s:.1f}s | ${result.cost_usd:.4f}"
              f"{' | BLOCKED' if result.blocked else ''}")
        print("   router.log:")
        for entry in router.log:
            print(f"     {entry['adapter']:<5} {entry['reason']:<20} {entry['sensitivity']:<10} "
                  f"blocked={entry['blocked']}  {entry['latency_s']:.1f}s")
        print()

    print(f"{matched}/{len(QUESTIONS)} answers matched | cloud calls: {cloud.calls}")
    return 1 if cloud.calls else 0


if __name__ == "__main__":
    sys.exit(main())
