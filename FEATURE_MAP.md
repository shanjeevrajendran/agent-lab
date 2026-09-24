# Feature Map — agent-lab

Purpose: turn a vague report ("routing looks wrong", "the agent loops") into a concrete file to investigate. Verify entries with the `control-agent-lab` skill; update this file when features change.

### Adapters (local and cloud)
- **User-facing description**: interchangeable stub models. Local is free and fast; cloud costs money and is slower. Both return scripted replies.
- **How to reach it**: `LocalAdapter(script).complete(messages, sensitivity)` and `CloudAdapter(script).complete(...)`. Only `router.py` may call `.complete(` (checked in CI); agents go through `Router.generate`. Try the snippet in `.claude/skills/control-agent-lab/SKILL.md`.
- **Key symbols**: `Adapter`, `_ScriptedAdapter`, `Reply`, `allowed` (levels each adapter may receive)
- **Owning files**: `adapters.py`
- **Common failure modes**: separate reply counters per adapter, so a case that flips adapters mid-loop replays its script; `PrivacyViolationError` (a `PermissionError`) when cloud receives `local_only`, which the agent loop logs and turns into `blocked=True`; passing a raw adapter to `run_agent` raises `AttributeError` (no `generate`, by design).

### Privacy / sensitivity
- **User-facing description**: every request carries a label (`local_only`, `cloud_safe`, `public`). Missing or unrecognized means `local_only`.
- **How to reach it**: pass a label as the last argument of `run_agent(model, question, sensitivity)` or `router.generate(messages, sensitivity)`.
- **Key symbols**: `Sensitivity`, `Sensitivity.parse`, `CloudAdapter.allowed`
- **Owning files**: `adapters.py` (enum, parse, cloud lock), `router.py` (first check), `PRIVACY.md` (definitions)
- **Common failure modes**: a typo'd label silently becomes local-only (intended, but surprising); labels are trusted, not verified; no sanitizer exists.

### Tools
- **User-facing description**: `calculator` (safe + - * / arithmetic) and `lookup` (synthetic fact table).
- **How to reach it**: the model replies `Action: calculator[17 * 3]`; the agent looks the name up in `TOOLS`. Or call `tools.calculator("17 * 3")` directly.
- **Key symbols**: `TOOLS`, `calculator`, `lookup`, `_FACTS`
- **Owning files**: `tools.py`
- **Common failure modes**: unsupported expressions return `error: ...` strings instead of raising; `lookup` misses return `not found`.

### ReAct agent loop
- **User-facing description**: model reasons, picks a tool, sees the result, repeats until `Final Answer:` or the step cap.
- **How to reach it**: `run_agent(model, question, sensitivity=None, max_steps=5)`; returns `AgentResult(answer, steps, cost_usd, latency_s, blocked)`.
- **Key symbols**: `run_agent`, `_ACTION`, `_FINAL` (reply-parsing regexes), `SYSTEM_PROMPT`
- **Owning files**: `agent.py`
- **Common failure modes**: malformed replies get an error observation and consume a step; hitting `max_steps` returns "(no answer: step limit reached)".

### Router
- **User-facing description**: picks local or cloud per call. Privacy first, then cost/latency (short prompt → local, long → cloud).
- **How to reach it**: `Router(local, cloud, long_prompt_chars=200)`; used as `model` in `run_agent`. Read `router.log` afterwards.
- **Key symbols**: `Router.choose`, `Router.generate`, `router.log` (adapter, reason, sensitivity, cost, latency)
- **Owning files**: `router.py`
- **Common failure modes**: the length threshold counts the system prompt, so short questions can still cross it after a few loop steps; prompt length is only a stand-in for difficulty.

### Eval harness
- **User-facing description**: runs synthetic cases and reports PASS/FAIL, adapters used, simulated cost and latency. A case fails on a wrong answer, unexpected routing, or a privacy leak.
- **How to reach it**: `python3 evals.py` (exit code 1 on any failure). Add cases in `cases.json`.
- **Key symbols**: `run_case`, `main`; case fields `id`, `question`, `sensitivity`, `script`, `expected`, `expect_cloud`, `long`, `note`
- **Owning files**: `evals.py`, `cases.json`
- **Common failure modes**: multi-step cases must stay on one adapter (see Adapters); cost/latency are simulated, not measured.
