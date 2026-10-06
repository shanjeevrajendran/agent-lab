# agent-lab

> **Status: complete (learning project).** It did its job; it is no longer being extended. The ideas carry over to a successor that is built from existing tools (Claude Code + Hermes Agent + Ollama) instead of hand-written ones. See [What it taught](#what-it-taught).

A small learning project that shows how an AI agent can use a cheap local model and a stronger cloud model **without leaking private data**. It has:

- a **ReAct agent**: it reasons, calls a tool, reads the result, and repeats until it has an answer,
- a **router** that picks the local or cloud model for each request, checking privacy first,
- an **eval harness** that tests all of this on synthetic examples.

The evals use stub (fake) models and made-up data, so they run with plain Python: no API keys, no installs, no network. An optional `live_check.py` runs real questions through the router to a local model served by [Ollama](https://ollama.com).

## Quick start

You need Python 3.10 or newer.

    git clone https://github.com/shanjeevrajendran/agent-lab.git
    cd agent-lab
    python3 evals.py

You should see:

    PASS  add-public                   local  $0.0000  0.10s
    ...
    8/8 passed | cost $0.0020 | latency 0.95s (simulated)

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
| `live_check.py` | Opt-in: real questions through the router to Ollama (not run in CI) |
| `.env.example` | Settings template (`LOCAL_MODEL`, `LOCAL_MODEL_URL`); copy to `.env` (git-ignored) |
| `config.py` | Reads `.env`; environment variables take priority |
| `.githooks/pre-commit`, `.github/workflows/ci.yml` | The pre-commit hook and the CI job |
| `PRIVACY.md` | The privacy rules |
| `FEATURE_MAP.md` | Where each feature lives and how it tends to break |
| `ENFORCEMENT.md` | Which rules are enforced automatically, and how strongly |
| `EVAL_PLAYBOOK.md` | How to test the agent-control skill before trusting it, plus the run log |
| `.claude/skills/control-agent-lab/` | Instructions for AI coding agents working on this project |

## Related

- [kb-mcp](https://github.com/shanjeevrajendran/kb-mcp) is a read-only MCP server over the knowledge graph I use to learn the concepts behind this project. Like this repo, it follows the local-only, fail-closed approach: stdio transport, no network calls, no writes.

## What it taught

| Phase | Where it lives | The lesson |
|---|---|---|
| LLM basics | `adapters.py` | One interface for any model; a real local model (Ollama) behind the same shape as the stubs ([#10](https://github.com/shanjeevrajendran/agent-lab/pull/10)) |
| Agent loop | `agent.py`, `tools.py` | ReAct as a plain loop with a step limit; a real model needs a tuned system prompt, a stop sequence and an output cap to follow the format ([#10](https://github.com/shanjeevrajendran/agent-lab/pull/10)) |
| Routing and privacy | `router.py`, `PRIVACY.md` | Privacy before cost; unknown labels fail closed; two locks (router + adapter); log before calling so blocked calls are audited ([#8](https://github.com/shanjeevrajendran/agent-lab/pull/8)) |
| Evals and enforcement | `evals.py`, `cases.json`, `check_router_bypass.py`, `ENFORCEMENT.md` | Assert on the decision log, not just the answer; every bug gets a case that fails on the old code (e.g. the system prompt counting toward prompt length, [#10](https://github.com/shanjeevrajendran/agent-lab/pull/10)) |
| Testing agents | `EVAL_PLAYBOOK.md` | Blinded tasks with a judge show whether a coding agent reproduces before it fixes ([#3](https://github.com/shanjeevrajendran/agent-lab/pull/3)-[#7](https://github.com/shanjeevrajendran/agent-lab/pull/7)) |

Left open on purpose, because mature tools already do them: a `cloud_safe` sanitizer (PII redaction), multi-agent orchestration, and a gateway with cost tracking.
