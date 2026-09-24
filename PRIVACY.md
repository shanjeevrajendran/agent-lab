# Privacy model

Every request carries a `sensitivity` label. The label decides where it may run.

| Level | Meaning | Allowed adapters |
|---|---|---|
| `local_only` | Contains private data. Never leaves this machine. | local |
| `cloud_safe` | Sanitized: identifying details removed or replaced. | local, cloud |
| `public` | Already public, or synthetic. | local, cloud |

Synthetic examples:
- `local_only`: "Summarize this note from Jane Doe's medical record."
- `cloud_safe`: "Summarize this note from [PATIENT]'s record." (name replaced)
- `public`: "What is 17 * 3?"

## Rules
1. **Unknown means local-only.** A missing, misspelled or unrecognised label is treated as `local_only` (`Sensitivity.parse`).
2. **Privacy is the router's first check**, before cost or latency. A `local_only` request is never sent to cloud, even if the local model is slower or weaker.
3. **Two locks.** The router avoids cloud for `local_only`, and `CloudAdapter` refuses it with a `PrivacyViolationError` anyway, so a routing bug cannot leak data. The agent loop logs the block loudly and returns a clean `blocked` result.
4. **The caller sanitizes.** Marking something `cloud_safe` is a promise that the caller already removed private details.

## Not covered (yet)
- No sanitizer is built; nothing checks that `cloud_safe` data is actually clean.
- Labels are trusted, not verified: a wrong `public` label will be honored.
