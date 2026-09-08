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
- Colors come from the established four-step palette (see Color System below); never break its ±1 adjacency rule.
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
- Rebuild retrieval index (needs a key; see Retrieval Layer): `OPENAI_API_KEY=... uv run python scripts/build_index.py`
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

## Settled Decisions & Invariants

Append-mostly decision log. Each entry states the rule *and* the why, so future sessions don't "fix" it. When a decision costs a debugging session or a design discussion, promote it here.

### Retrieval Layer

Replies are grounded in public-domain psychoanalytic texts (Freud trans. Eder/Brill/Hall, Jung trans. Hinkle — NEVER the Strachey Standard Edition, which is still copyrighted). Invariants:

- **Same embedding model on both sides.** The corpus (`scripts/build_index.py`) and the runtime query (`api/index.py`) must use the same model; both files carry paired `EMBEDDING PROVIDER` comment-toggles (OpenAI default, Voyage alternative). The runtime asserts dimension equality.
- **Offline/online split.** Embeddings are precomputed and committed (`api/_index/embeddings.npy` float16 row-normalized + `chunks.json`); the runtime embeds only the query — never load model weights into the function, never add a vector DB at this corpus size (pgvector is the known later upgrade path).
- **Graceful degradation.** Missing index or failed embedding call → ungrounded chat, never a 500.
- **Persona survives grounding.** Retrieved passages are appended to the system prompt under `GROUNDING_PREAMBLE`, which re-asserts the 1–3 sentence limit and forbids mentioning sources.
- **Corpus pruning.** Per-book `start`/`end` regex markers in `BOOKS` cut title pages, TOCs, translator boilerplate, and indices before chunking; substantive prose (author prefaces, Hinkle's analytical introduction) stays. Pruning lives in the script — never hand-edit the committed source texts, they must stay byte-identical to a fresh fetch.
- **Rate limits.** Embedding requests are token-budgeted (≤25K est. tokens each) and paced via `TPM_LIMIT` (40K, the OpenAI free tier) with retry-on-429; raise `TPM_LIMIT` on paid tiers.

### Cost & Abuse Guards

`/api/chat` is a public endpoint spending real credit. Three guards, sized so a
human conversing in good faith never notices them: history trimmed to the last
`HISTORY_MAX_MESSAGES` (20), per-message truncation at `MESSAGE_MAX_CHARS`
(2000), and a sliding 60-second per-IP window at `RATE_LIMIT_PER_MINUTE` (15).
All three run *before* anything touches a paid API.

- **The rate limiter is best-effort by design.** `_RATE_BUCKETS` is module
  state, so it is per serverless instance: it does not survive cold starts and
  is not shared across concurrent instances. That is an accepted trade-off at
  this scale, not an oversight — it defeats casual scripting, which is all it
  is for. Do not add Redis/Upstash to "fix" it unless the traffic justifies the
  dependency; that is the known upgrade path if it ever does.

### Mobile Viewport & Safe Areas

- **Never use `h-screen` for the app shell.** `100vh` is the *layout* viewport
  on mobile: it ignores the on-screen keyboard, which pushes the footer (and
  the send button) below the visible area. The shell uses `.app-viewport`
  (`100dvh`, with a `100vh` line first as the pre-`dvh` fallback).
- **`pb-safe` and `viewport-fit=cover` are coupled.** `env(safe-area-inset-*)`
  resolves to 0 without `viewport-fit=cover` in the `viewport` export in
  `app/layout.tsx`. Removing one silently disables the other.
- The `min-w-0` on the textarea is defensive only. It was *not* the cause of
  the off-screen send button: verified with Playwright from 240px to 414px,
  with and without the class, results identical. Don't cite it as the fix.

### Accessibility

- **The transcript must not be a live region.** The typewriter mutates the last
  bubble ~40×/second; `aria-live` on `<main>` (or `role="log"`, whose implicit
  live region is the same trap) makes a screen reader read partial words
  continuously. Announcements go through the separate `sr-only`
  `aria-live="polite"` region, which carries only completed replies.
- **`usePrefersReducedMotion()` exists because CSS can't reach the typewriter.**
  The blanket `prefers-reduced-motion` block in `globals.css` handles the
  declarative animations; the JS timer needs the value in React. Keep the
  reduced-motion path routed through the same timer so the queued closing line
  still fires.

### Color System

Four discrete steps — **every touching surface pair must be exactly ±1 step**:

| Step | Hex | Role |
|---|---|---|
| 1 | `#D45F2A` | Page background (burnt orange) |
| 2 | `#EDA551` | Header, user bubbles, user avatar (warm amber) |
| 3 | `#F9D074` | Message area, send button (warm yellow) |
| 4 | `#F8F0E4` | AI bubbles, input footer, textarea (warm cream) |
| Accent | `#E2C3DA` | Focus rings, decorative borders (dusty mauve) |

Contact graph (for reference when adding new surfaces):
```
page bg (1) ↔ header (2) ↔ message area (3) ↔ AI bubbles (4)
                                            ↔ user bubbles (2)
                                            ↔ footer (4) ↔ textarea (4)
                                                          ↔ send btn (3)
```

### Avatar System

Avatars use **Twemoji SVGs** (jsDelivr CDN, v14.0.2) loaded as `<img>` elements — not system emoji glyphs. This eliminates platform-specific font rendering differences (Apple vs Windows vs Android emoji).

- Analyst avatar: 🧐 `U+1F9D0` → `1f9d0.svg`
- User avatar: 😰 `U+1F630` → `1f630.svg`
- `EMOJI_SCALE = '109%'` — a geometric constant: `1 / (33/36)`, where 33/36 is the Twemoji face-to-viewBox ratio. Do not change this to a platform-tuned magic number.
- The avatar `<div>` uses `overflow-visible` + `rounded-full` so the face fills the circle border and minor extrusions (monocle chain, sweat bead) escape naturally.

All three avatar constants live at the top of `frontend/components/ChatInterface.tsx` and are shared via the `Avatar` component. Do not inline sizes or positions at call-sites.
