"""Eval harness: run synthetic cases through the agent, score them, print a report.

A case passes only if the answer is right, the routing is as expected (cloud used only
when the case says so), and privacy holds. Privacy is asserted on the router's decision
log and the cloud adapter's call counter, not just the final answer.
"""
import json
import sys
from pathlib import Path

from adapters import CloudAdapter, LocalAdapter, Sensitivity
from agent import run_agent
from router import DEFAULT_LONG_PROMPT_CHARS, PRIVACY_REASON, Router

CASES = Path(__file__).with_name("cases.json")


def _fail(case: dict, note: str, used: str = "-") -> dict:
    return {"id": case["id"], "passed": False, "used": used, "cost": 0.0,
            "latency": 0.0, "note": note}


def run_case(case: dict) -> dict:
    script, question = case["script"], case["question"]

    # "long" cases depend on the router's provisional length threshold. If it changes or is
    # replaced (e.g. by a task envelope), these cases need re-checking.
    if case.get("long") and len(question) < 2 * DEFAULT_LONG_PROMPT_CHARS:
        return _fail(case, "prompt is under 2x the router length threshold; re-check")

    # Scripted adapters count replies separately, so multi-step cases must stay on one
    # adapter. Only single-step cases use the real length threshold.
    threshold = DEFAULT_LONG_PROMPT_CHARS if len(script) == 1 else 10**6
    cloud = CloudAdapter(script)
    router = Router(LocalAdapter(script), cloud, long_prompt_chars=threshold)
    sensitivity = case.get("sensitivity")
    private = Sensitivity.parse(sensitivity) is Sensitivity.LOCAL_ONLY

    try:
        result = run_agent(router, question, sensitivity)
    except PermissionError as e:  # the cloud adapter's second lock fired
        return _fail(case, f"blocked: {e} (cloud invoked {cloud.calls}x)")

    used = {e["adapter"] for e in router.log}
    correct = result.answer.strip().lower() == case["expected"].strip().lower()
    # Local-only requests: cloud never invoked, and every routing decision is local,
    # made for privacy reasons.
    leaked = private and (cloud.calls > 0 or "cloud" in used)
    decided_by_privacy = not private or (
        bool(router.log)
        and all(e["adapter"] == "local" and e["reason"] == PRIVACY_REASON for e in router.log)
    )
    routed_ok = ("cloud" in used) == bool(case.get("expect_cloud"))

    note = "" if correct else f"got {result.answer!r}"
    if leaked:
        note += " PRIVACY LEAK"
    elif not decided_by_privacy:
        note += " local-only not routed by privacy"
    elif not routed_ok:
        note += " unexpected routing"
    return {"id": case["id"],
            "passed": correct and routed_ok and not leaked and decided_by_privacy,
            "used": ",".join(sorted(used)), "cost": result.cost_usd,
            "latency": result.latency_s, "note": note.strip()}


def main() -> int:
    results = [run_case(c) for c in json.loads(CASES.read_text())]
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"{status}  {r['id']:<28} {r['used']:<6} ${r['cost']:.4f}  {r['latency']:.2f}s  {r['note']}")
    passed = sum(r["passed"] for r in results)
    print(f"\n{passed}/{len(results)} passed | "
          f"cost ${sum(r['cost'] for r in results):.4f} | "
          f"latency {sum(r['latency'] for r in results):.2f}s (simulated)")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
