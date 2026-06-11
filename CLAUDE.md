## Rules to Follow

- You must always commit your changes whenever you update code.
- You must always try and write code that is well documented. (self or commented is fine)
- You must only work on a single feature at a time.
- You must explain your decisions thoroughly to the user.

### Rules for Frontend

- You must pay attention to visual clarity and contrast. Do not place white text on a white background.
- You must ensure the UX is pleasant. Boxes should grow to fit their contents, etc.
- When asking the user for sensitive information - you must use password style text-entry boxes in the UI.
- You should use Next.js as it works best with Vercel.
- The nextjs docs are at https://nextjs.org/docs. Review them as necessary.
- This frontend will ultimately be deployed on Vercel, but it should be possible to test locally.
- The Vercel docs are at https://vercel.com/docs. Review them as necessary.
- Always provide users with a way to run the created UI once you have created it.
- The project's color scheme is a four-step warm palette. Every pair of touching surfaces must be exactly ±1 step apart. Do not break this adjacency rule.

### README.md Rules

- When you create README.md's - they should be dope, and use fun and approachable language.
- While being fun, they should remain technically accurate, focused, instructive, and concise.

---

## Current App: "The Analyst"

This is a psychoanalyst-themed chat interface. The persona is a stern, sinister continental psychoanalyst — clinical, cold, and slightly menacing. The user is framed as an anxious wreck seeking (perhaps unwanted) insight.

### Architecture

| Layer | Technology | Location |
|---|---|---|
| Frontend | Next.js 14 + TypeScript + Tailwind CSS | `frontend/` |
| Backend | FastAPI + Anthropic (`claude-haiku-4-5-20251001`, OpenAI swappable via comment toggle) | `api/` |
| Retrieval | numpy cosine over precomputed OpenAI `text-embedding-3-small` vectors | `api/_index/`, `scripts/build_index.py` |
| Deploy | Vercel monorepo | `vercel.json` |

`vercel.json` routes `/api/*` to the Python serverless backend and everything else to the Next.js app. The `includeFiles` config on the Python build bundles `api/_index/**` into the serverless function.

### Retrieval Layer

Replies are grounded in public-domain psychoanalytic texts (Freud trans. Eder/Brill/Hall, Jung trans. Hinkle — NEVER the Strachey Standard Edition, which is still copyrighted). Invariants:

- **Same embedding model on both sides.** The corpus (`scripts/build_index.py`) and the runtime query (`api/index.py`) must use the same model; both files carry paired `EMBEDDING PROVIDER` comment-toggles (OpenAI default, Voyage alternative). The runtime asserts dimension equality.
- **Offline/online split.** Embeddings are precomputed and committed (`api/_index/embeddings.npy` float16 row-normalized + `chunks.json`); the runtime embeds only the query — never load model weights into the function, never add a vector DB at this corpus size (pgvector is the known later upgrade path).
- **Graceful degradation.** Missing index or failed embedding call → ungrounded chat, never a 500.
- **Persona survives grounding.** Retrieved passages are appended to the system prompt under `GROUNDING_PREAMBLE`, which re-asserts the 1–3 sentence limit and forbids mentioning sources.
- Rebuild: `OPENAI_API_KEY=... uv run python scripts/build_index.py` (idempotent; `--chunks-only` skips the embedding step).

### Established Color System

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