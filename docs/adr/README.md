# Architecture Decision Records

Decisions that are **settled**, scoped to one subsystem, and expensive to
rediscover. Each record states the rule *and* the reasoning, so a future session
(human or model) doesn't "fix" something that was deliberate.

These live here rather than in `CLAUDE.md` because that file is loaded into
context on every session: it should carry what is always relevant, while
subsystem detail is read on demand by whoever is actually touching that
subsystem. `CLAUDE.md` keeps a one-line tripwire per record pointing here.

| # | Decision | Read before touching |
|---|---|---|
| [0001](0001-four-step-colour-palette.md) | Four-step colour palette, every touching surface pair exactly ±1 | any colour, new surface, or generated asset |
| [0002](0002-twemoji-avatars.md) | Avatars are Twemoji SVGs; `EMOJI_SCALE` is geometric, not tuned | the `Avatar` component, icons, favicon |
| [0003](0003-retrieval-layer.md) | Public-domain corpus only (never Strachey); numpy, not a vector DB | `scripts/build_index.py`, `api/index.py`, `api/_index/` |
| [0004](0004-cost-and-abuse-guards.md) | History/message/rate guards; the limiter is best-effort by design | `api/index.py` guards, anything about rate limiting |
| [0005](0005-mobile-viewport-and-safe-areas.md) | `100dvh` not `h-screen`; `pb-safe` requires `viewport-fit=cover` | the app shell, footer padding, viewport meta |
| [0006](0006-accessibility-live-region-and-reduced-motion.md) | Announce completed replies only; reduced motion in CSS *and* JS | the transcript, typewriter, any animation |

## Writing a new one

Copy [`TEMPLATE.md`](TEMPLATE.md), take the next number, add a row above.
Promote a decision here when it cost a debugging session or a design argument —
that is the same bar `CLAUDE.md` uses. Supersede rather than delete: set the old
record's status to `Superseded by ADR-00NN` and leave it in place, because the
reasoning that was *rejected* is often the useful part.

Records are numbered by when the decision landed, not when it was written down;
0001–0004 were recorded retroactively from `CLAUDE.md` on 2026-09-08.
