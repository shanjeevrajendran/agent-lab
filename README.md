# agent-lab

A small learning project that shows how an AI agent can use a cheap local model and a stronger cloud model **without leaking private data**. It has:

- a **ReAct agent**: it reasons, calls a tool, reads the result, and repeats until it has an answer,
- a **router** that picks the local or cloud model for each request, checking privacy first,
- an **eval harness** that tests all of this on synthetic examples.

Everything uses stub (fake) models and made-up data, so it runs with plain Python: no API keys, no installs, no network.

## Quick start

You need Python 3.10 or newer.

    git clone https://github.com/shanjeevrajendran/agent-lab.git
    cd agent-lab
    python3 evals.py

You should see:

    PASS  add-public                   local  $0.0000  0.10s
    ...
    7/7 passed | cost $0.0020 | latency 0.90s (simulated)

Each line is one test case: whether it passed, which model it used, and its (simulated) cost and time. The command exits with code 1 if any case fails.

## How a request flows

    evals.py -> agent.py (ReAct loop) -> router.py -> adapters.py (local or cloud model)
                     |
                  tools.py (calculator, lookup)

1. The agent sends the conversation to the router, with a **sensitivity label**.
2. The router checks privacy first. Private or unlabeled data always goes to the local model.
3. Otherwise it picks by size: short prompts go local (free, fast), long prompts go to cloud (paid, stronger).
4. The router writes every decision to `router.log`, including calls that were blocked.
5. If the model asks for a tool (`Action: calculator[17 * 3]`), the agent runs it and sends back the result.

## Privacy labels

| Label | Meaning | Can use cloud? |
|---|---|---|
| `local_only` | Private data | No |
| `cloud_safe` | Private details already removed | Yes |
| `public` | Public or synthetic | Yes |

- A missing or misspelled label is treated as `local_only`.
- Two locks: the router keeps private data local, and the cloud adapter refuses it anyway. A refused call stops the request cleanly and is logged as `PRIVACY BLOCK`.
- Full rules: [PRIVACY.md](PRIVACY.md).

## Try one request yourself

    python3 -c "
    from adapters import LocalAdapter, CloudAdapter
    from router import Router
    from agent import run_agent
    r = Router(LocalAdapter(['Final Answer: ok']), CloudAdapter(['Final Answer: ok']))
    print(run_agent(r, 'What is 2 + 2?', 'local_only'))
    print(r.log)
    "

Change `'local_only'` to `'public'`, `None` or a typo, or make the question longer than 200 characters, and watch the router's `reason` change.

## Making changes

- **Add a test case:** add an entry to `cases.json` and run `python3 evals.py`.
- **Enable the pre-commit hook (once per clone):** `git config core.hooksPath .githooks`. It runs the evals before every commit and blocks the commit if any case fails.
- **CI:** every push to `main` and every pull request runs the evals and `check_router_bypass.py` (which fails if code other than the router talks to a model directly).
- **`main` is protected:** changes land through a pull request once CI passes. Direct pushes are rejected.

## Files

| File | What it does |
|---|---|
| `adapters.py` | The model interface, the privacy labels, and the stub local and cloud models |
| `router.py` | Picks local or cloud (privacy first) and logs every decision |
| `agent.py` | The ReAct loop |
| `tools.py` | Toy tools: `calculator` and `lookup` |
| `evals.py`, `cases.json` | The test harness and its synthetic cases |
| `check_router_bypass.py` | CI check that nothing bypasses the router |
| `.env.example` | Placeholder settings; copy to `.env` (git-ignored) when real models are added |
| `.githooks/pre-commit`, `.github/workflows/ci.yml` | The pre-commit hook and the CI job |
| `PRIVACY.md` | The privacy rules |
| `FEATURE_MAP.md` | Where each feature lives and how it tends to break |
| `ENFORCEMENT.md` | Which rules are enforced automatically, and how strongly |
| `EVAL_PLAYBOOK.md` | How to test the agent-control skill before trusting it, plus the run log |
| `.claude/skills/control-agent-lab/` | Instructions for AI coding agents working on this project |

## Next steps

- Swap a stub model for a real one (copy `.env.example` to `.env` and put keys there; `.env` is never committed).
- Add a sanitizer so `cloud_safe` data is actually checked, not just trusted.
