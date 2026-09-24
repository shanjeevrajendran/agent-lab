# Enforcement Ladder — agent-lab

Rungs, strongest to weakest: 1 architecture, 2 types/static analysis, 3 CI hard-fail, 4 rules/skills/docs, 5 human review.
Operating rule: whenever you correct the same thing twice, move it up a rung instead of repeating the correction.

## Where each rule lives today

| Rule | Current enforcement | Rung | Status |
|---|---|---|---|
| Cloud never receives `local_only` data | `CloudAdapter.allowed` raises `PrivacyViolationError` | 1 | Strong. The router logs the decision before calling the adapter, so a refused call leaves a `blocked: True` entry in `router.log`; the agent loop logs `PRIVACY BLOCK` and returns a clean `blocked` result; evals fail the case. |
| Missing or typo'd label means `local_only` | `Sensitivity.parse` fails closed, plus two eval cases | 1 | Strong. Eval cases only run when someone runs them. |
| Router checks privacy before cost | Code order, `PRIVACY.md`, and eval asserts on the router log (adapter=local, reason=privacy) plus the cloud call counter, including case `note-local-only-long` | 3 | Covered: evals run in CI and branch protection blocks merges on failure. Before the long case was added, the evals passed 6/6 with the privacy check removed. |
| `.env` is never committed | `.gitignore` | 3 (in intent) | Active: repo initialized and pushed; no `.env` was staged in the first commit. |
| Evals must pass before changes land | `.githooks/pre-commit` runs `python3 evals.py` and blocks the commit on failure | 3 | Covered twice. Local hook: verified with a seeded bug in a scratch copy. CI (`.github/workflows/ci.yml`, on push to `main` and PRs): verified red on a seeded privacy bug. The hook can be skipped with `--no-verify`; CI cannot. |
| `main` only changes through passing CI | Branch protection on `main`: requires the `checks` job, applies to admins, no force-push or deletion | 3 | Covered; verified: a direct push was rejected (`GH006 ... Required status check "checks" is expected`). |
| Nothing bypasses the router | Adapters expose `complete`, not `generate`, so a raw adapter passed to `run_agent` raises `AttributeError` (rung 1). `check_router_bypass.py` fails CI on any `.complete(` call or `def generate` outside `router.py` (rung 3). | 1 and 3 | Covered; verified with seeded `.complete(` calls, `def generate` and `async def generate`, and raw adapters as the model. Remaining limit: name-based, so `getattr(adapter, "comp" + "lete")` would slip past the check. |
| Agents verify with real output | `control-agent-lab` skill | 4 | Tested: Tasks A and B of `EVAL_PLAYBOOK.md` passed (B also blinded and after the rule-3 change). Still a default, not enforced; re-run the playbook when the skill or model changes. |

## Promotion candidates

1. ~~Make evals catch a wrong check order.~~ Done: `note-local-only-long` is over 2x the length threshold and the evals assert on the decision log. The case depends on the provisional length heuristic; re-check it when that is replaced.
2. ~~Give evals a hard-fail home.~~ Done: pre-commit hook, a GitHub Actions job, and branch protection requiring the `checks` job.
3. ~~Add a banned-pattern check.~~ Done as a second CI step (`check_router_bypass.py`; the only allowlisted file is `router.py`), and the raw-adapter case is now structural (adapters have no `generate`).
4. ~~Typed privacy error.~~ Done: the adapter lock raises `PrivacyViolationError` (a `PermissionError` subclass), `run_agent` catches it, logs `PRIVACY BLOCK` at ERROR and returns `blocked=True`. Evals fail a blocked case and still assert on the cloud call counter and decision log, so a swallowed block cannot pass as handled.

## Quick audit (run periodically)

- [ ] List the corrections you made or an agent made in the last 10-20 changes.
- [ ] For each one, ask which rung it should live on.
- [ ] Anything said twice: promote it this cycle.
