# ADR-0004: Cost and abuse guards, deliberately best-effort

- **Status:** Accepted
- **Decided:** 2026-06-11 (`6aec2b6`)
- **Recorded:** 2026-09-08 — written retroactively from CLAUDE.md
- **Applies to:** `api/index.py`

## Context

`/api/chat` and `/api/notes` are public endpoints on a personal deployment that
spend real credit on every call. Without limits, a single script — or one very
long pasted message — can run up a bill. The counter-pressure is that a human
having a genuine conversation must never bump into a guard.

## Decision

Three guards, all evaluated **before anything touches a paid API**:

| Guard | Constant | Value |
|---|---|---|
| History trim | `HISTORY_MAX_MESSAGES` | 20 most recent messages reach the model |
| Per-message cap | `MESSAGE_MAX_CHARS` | 2,000 characters, silently truncated |
| Per-IP rate limit | `RATE_LIMIT_PER_MINUTE` | 15, sliding 60-second window |

**The rate limiter is best-effort by design.** `_RATE_BUCKETS` is module state,
so it is scoped to a single serverless instance: it does not survive cold starts
and is not shared between concurrent instances. This is an accepted trade-off,
not an oversight. Its job is to defeat casual scripting, and it does that.

## Consequences

- A determined attacker with distributed IPs, or one who exploits cold starts, is
  not stopped. Accepted at this scale.
- **Do not add Redis/Upstash to "fix" this** unless real traffic justifies the
  dependency — that is the known upgrade path, not a pending task.
- Truncation is silent by design: a user who pastes an essay gets a reply to the
  first 2,000 characters rather than an error.
- The guards are covered by tests (`tests/test_guards.py`), so tightening or
  loosening a value is a deliberate, visible change.
