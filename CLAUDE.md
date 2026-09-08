# The Analyst

A psychoanalyst-themed chat interface. The persona is a stern, sinister continental psychoanalyst — clinical, cold, and slightly menacing. The user is framed as an anxious wreck seeking (perhaps unwanted) insight.

## Rules to Follow

- You must always commit your changes whenever you update code.
- You must always try and write code that is well documented. (self or commented is fine)
- You must only work on a single feature at a time.
- You must explain your decisions thoroughly to the user.
- You must follow TDD patterns when reasonable.
- When something fails, report the actual error output — never paper over a failing test or skipped step.
- Do not add dependencies without stating why the standard library / existing deps can't do it.

### Rules for Frontend

- You must pay attention to visual clarity and contrast. Do not place white text on a white background.
- You must ensure the UX is pleasant. Boxes should grow to fit their contents, etc.
- When asking the user for sensitive information - you must use password style text-entry boxes in the UI.
- You should use Next.js as it works best with Vercel.
- The nextjs docs are at https://nextjs.org/docs. Review them as necessary.
- This frontend will ultimately be deployed on Vercel, but it should be possible to test locally.
- The Vercel docs are at https://vercel.com/docs. Review them as necessary.
- Always provide users with a way to run the created UI once you have created it.
- Colors come from the established four-step palette ([ADR-0001](docs/adr/0001-four-step-colour-palette.md)); never break its ±1 adjacency rule.
- Any copy that you write is a placeholder. Keep it brief and surface it to the user.

### README.md Rules

- When you create README.md's - they should be dope, and use fun and approachable language.
- While being fun, they should remain technically accurate, focused, instructive, and concise.

## Architecture

| Layer | Technology | Location |
|---|---|---|
| Frontend | Next.js 14 + TypeScript + Tailwind CSS | `frontend/` |
| Backend | FastAPI + Anthropic (`claude-haiku-4-5-20251001`, OpenAI swappable via comment toggle) | `api/` |
| Retrieval | numpy cosine over precomputed OpenAI `text-embedding-3-small` vectors | `api/_index/`, `scripts/build_index.py` |
| Deploy | Vercel monorepo | `vercel.json` |

`vercel.json` routes `/api/*` to the Python serverless backend and everything else to the Next.js app. The `includeFiles` config on the Python build bundles `api/_index/**` into the serverless function.

## Commands

All test/build commands run keyless — external clients are mocked. Keep it that way.

- Backend dev server (from repo root): `uv run uvicorn api.index:app --reload` → `http://localhost:8000`
- Frontend dev server: `npm run dev` in `frontend/` → `http://localhost:3000` (proxies `/api/*` to the backend on :8000, so run both)
- Backend tests (from repo root): `uv run pytest -q`
- Frontend tests: `npm test` in `frontend/`
- Lint / build: `npm run lint` / `npm run build` in `frontend/`
- Rebuild retrieval index (needs a key; [ADR-0003](docs/adr/0003-retrieval-layer.md)): `OPENAI_API_KEY=... uv run python scripts/build_index.py`
- Deploy: push to `main` (Vercel builds from the repo)

UI behaviour that tests can't reach (layout at a given viewport, live regions,
reduced motion) is verified by driving the dev server with Playwright and
intercepting `**/api/chat` with a canned `{"reply": "…"}` — keyless, like
everything else. Playwright is a machine-level tool, deliberately not a project
dependency; the headless-shell build isn't installed, so launch with
`channel="chromium"`.

## Gotchas

- Backend commands run from the repo root, not `api/` — the module path is `api.index:app` and pytest discovers `tests/` from the root.
- Requires Python ≥3.12,<3.13 (pinned in `pyproject.toml`); use `uv`, not a system pip.
- The frontend in dev is useless without the backend running — `/api/*` proxies to :8000 and chat requests will fail otherwise.
- **Never run `npm run build` while `npm run dev` is running.** They share
  `frontend/.next`, and the production build leaves the dev server serving 500s
  with no obvious cause. Recovery: stop dev, `rm -rf frontend/.next`, restart.
  Symptom looks like the app suddenly lost its DOM — it hasn't.

## Settled Decisions & Invariants

Subsystem decisions live in [`docs/adr/`](docs/adr/README.md) — full reasoning,
read on demand. Below is one tripwire line each: if you are about to touch the
subsystem in the right-hand column, read that record **first**.

| Tripwire | Record | Before touching |
|---|---|---|
| Every touching surface pair is exactly ±1 palette step | [ADR-0001](docs/adr/0001-four-step-colour-palette.md) | any colour, new surface, generated asset |
| Avatars are Twemoji SVGs; `EMOJI_SCALE` is geometric, not tuned | [ADR-0002](docs/adr/0002-twemoji-avatars.md) | the `Avatar` component, icons, favicon |
| Public-domain translations only — **never Strachey**; same embedding model both sides; no vector DB | [ADR-0003](docs/adr/0003-retrieval-layer.md) | `scripts/build_index.py`, `api/index.py`, `api/_index/` |
| The per-IP rate limiter is best-effort **by design** — don't "fix" it with a dependency | [ADR-0004](docs/adr/0004-cost-and-abuse-guards.md) | the guards in `api/index.py` |
| Never `h-screen` for the shell (use `100dvh`); `pb-safe` needs `viewport-fit=cover` | [ADR-0005](docs/adr/0005-mobile-viewport-and-safe-areas.md) | app shell, footer padding, viewport meta |
| The transcript must **not** be a live region; reduced motion needs CSS *and* JS | [ADR-0006](docs/adr/0006-accessibility-live-region-and-reduced-motion.md) | transcript, typewriter, any animation |

When a decision costs a debugging session or a design discussion, write it up as
a new ADR (copy `docs/adr/TEMPLATE.md`) and add a tripwire row here. Keep this
table to one line per record — the detail belongs in the record.
