# Enforcement Ladder — agent-lab

Rungs, strongest to weakest: 1 architecture, 2 types/static analysis, 3 CI hard-fail, 4 rules/skills/docs, 5 human review.
Operating rule: whenever you correct the same thing twice, move it up a rung instead of repeating the correction.

## Where each rule lives today

| Rule | Current enforcement | Rung | Status |
|---|---|---|---|
| Cloud never receives `local_only` data | `CloudAdapter.allowed` raises `PermissionError` | 1 | Strong. Fails loudly at runtime. |
| Missing or typo'd label means `local_only` | `Sensitivity.parse` fails closed, plus two eval cases | 1 | Strong. Eval cases only run when someone runs them. |
| Router checks privacy before cost | Code order, `PRIVACY.md`, and eval asserts on the router log (adapter=local, reason=privacy) plus the cloud call counter, including case `note-local-only-long` | 4 (rung 3 once evals run in CI) | Covered. Before this was added, the evals passed 6/6 with the privacy check removed. |
| `.env` is never committed | `.gitignore` | 3 (in intent) | Active: repo initialized and pushed; no `.env` was staged in the first commit. |
| Evals must pass before changes land | `.githooks/pre-commit` runs `python3 evals.py` and blocks the commit on failure | 3 (local) | Covered twice. Local hook: verified with a seeded bug in a scratch copy. CI (`.github/workflows/ci.yml`, on push to `main` and PRs): verified red on a seeded privacy bug. The hook can be skipped with `--no-verify`; CI cannot, but it only blocks merges if branch protection requires the `checks` job (not enabled). |
| Nothing bypasses the router | `check_router_bypass.py` fails CI if `.generate(` is called outside `router.py` and `agent.py` | 3 | Covered; verified red on a seeded direct call. Limit: cannot catch a raw adapter passed to `run_agent` as the model. |
| Agents verify with real output | `control-agent-lab` skill | 4 | Default only; untested until the eval playbook is run. |

## Promotion candidates

1. ~~Make evals catch a wrong check order.~~ Done: `note-local-only-long` is over 2x the length threshold and the evals assert on the decision log. The case depends on the provisional length heuristic; re-check it when that is replaced.
2. ~~Give evals a hard-fail home.~~ Done: pre-commit hook plus a GitHub Actions job. Remaining (optional): branch protection requiring the `checks` job, so a red run blocks merges.
3. ~~Add a banned-pattern check.~~ Done as a second CI step (`check_router_bypass.py`; allowlist is `router.py` and `agent.py`). Remaining (optional): also catch a raw adapter passed to `run_agent` as the model.
4. *(Optional)* **Typed privacy error.** Raise a `PrivacyViolationError` from the adapter's second lock, catch it at the loop boundary and log it loudly: a clean failure for the user, fail-closed internally.

## Quick audit (run periodically)

- [ ] List the corrections you made or an agent made in the last 10-20 changes.
- [ ] For each one, ask which rung it should live on.
- [ ] Anything said twice: promote it this cycle.

## Note on the eval playbook

`EVAL_PLAYBOOK.md` Task A (seeded routing bug) assumed the evals reproduce a swapped check order. That was false until candidate 1 was done; it is now valid, and should be confirmed by running the mutation check.
