---
name: control-agent-lab
description: Run and verify the real agent-lab project (ReAct agent, privacy-aware router, eval harness) — execute the evals and a live router call, read the actual output, and report evidence instead of guessing. Use whenever asked to fix a bug, verify a change, or check routing/privacy behavior in agent-lab.
---

# Control agent-lab

CLI project, Python 3, no installs, no network. Run everything from the project root.

## Launch

- Full check: `python3 evals.py` (prints PASS/FAIL per case plus totals; exit code 1 on any failure).
- One request through the router with a chosen sensitivity (synthetic data only):

      python3 -c "
      from adapters import LocalAdapter, CloudAdapter
      from router import Router
      from agent import run_agent
      r = Router(LocalAdapter(['Final Answer: ok']), CloudAdapter(['Final Answer: ok']))
      print(run_agent(r, 'What is 2 + 2?', 'local_only'))
      print(r.log)
      "

  Change the last argument of `run_agent` to `public`, `cloud_safe`, `None` or a typo and re-run to see routing change.

## Interact

- Read the real output. Do not paraphrase or assume; quote the PASS/FAIL lines.
- To add a scenario, add an object to `cases.json` (fields: `id`, `question`, `sensitivity`, `script`, `expected`, optional `expect_cloud`, `long` (asserts the prompt is 2x the router threshold), `note`) and re-run `python3 evals.py`.

## Capture evidence

- **Wrong answer**: the `note` column shows `got '...'`; read `agent.py` only after you have seen the failing output.
- **Routing/privacy**: inspect `router.log` (adapter, reason, sensitivity per call). `reason` says whether privacy or cost decided. A `PRIVACY BLOCK` line on stderr and `blocked=True` on the result mean a privacy lock fired.
- **Crash**: capture the full traceback, not just the last line.

## Verify, don't assert

1. Reproduce the reported behavior first, with output, before editing code.
2. After a change, re-run the same command and show the new output.
3. If you cannot reproduce it, say so. Do not guess a cause.
4. Privacy changes must keep `local_only`, unlabeled and misspelled labels off the cloud adapter. Confirm with `python3 evals.py`.

## Known gotchas

- Models are stubs with scripted replies. Cost and latency are simulated numbers, not measurements.
- Local and cloud stub adapters keep separate reply counters, so a multi-step case that flips adapters mid-loop replays the script from the start. `evals.py` pins multi-step cases to one adapter for this reason.
- The router picks cloud for long prompts (default 200 chars, counting the system prompt). Short cases stay local by default.
- `Sensitivity.parse` fails closed: missing or unrecognized labels become `local_only`.
- Running Python creates `__pycache__/`; it is safe to ignore.
