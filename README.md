# agent-lab

A tiny learning project: a ReAct agent, a privacy-aware router, and an eval harness.
Everything uses stub models and synthetic data, so it runs with no keys or installs.

## Run

    python3 evals.py

Prints PASS/FAIL per case plus total (simulated) cost and latency. Exits non-zero on any failure.

## Enable the pre-commit hook (once per clone)

    git config core.hooksPath .githooks

Runs `python3 evals.py` before every commit and blocks the commit if any case fails.

## Files

| File | Job |
|---|---|
| `adapters.py` | Shared model interface, `Sensitivity` levels, stub local and cloud adapters |
| `tools.py` | Toy tools: `calculator`, `lookup` |
| `agent.py` | ReAct loop: reason, call a tool, observe, repeat |
| `router.py` | Privacy check first, then cost/latency; logs every decision |
| `evals.py` | Runs `cases.json`, scores answers, routing and privacy |
| `cases.json` | Synthetic test cases |
| `PRIVACY.md` | What `local_only`, `cloud_safe` and `public` mean |

## Flow

    evals -> agent loop -> router -> adapter (local or cloud)
                 |
               tools

## Next steps

- Swap a stub adapter for a real one (keys go in `.env`, which is git-ignored).
- Add a sanitizer so `cloud_safe` is checked, not just trusted.
