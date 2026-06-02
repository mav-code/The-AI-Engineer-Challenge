# 🧐 The Analyst — Frontend

A warm, orange-to-cream chat interface for your stern, sinister AI psychoanalyst. Built with **Next.js 14**, **TypeScript**, and **Tailwind CSS**. The Analyst will see you now. Sit down. Do not touch anything.

## Running Locally

You need **two terminals** — one for the backend, one for the frontend.

### Terminal 1 – Backend (FastAPI)

From the repo root:

```bash
export OPENAI_API_KEY=sk-your-key-here
uv run uvicorn api.index:app --reload
```

The API will be live at `http://localhost:8000`.

### Terminal 2 – Frontend (Next.js)

```bash
cd frontend
npm install      # first time only
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) and begin your session. (If port 3000 is already taken, Next.js will use 3001 — check your terminal output.)

> The frontend automatically proxies `/api/*` requests to port 8000 during development, so no extra config is needed.

## Project Structure

```
frontend/
├── app/
│   ├── globals.css           # Tailwind base + scrollbar suppression
│   ├── layout.tsx            # Root layout + metadata
│   └── page.tsx              # Entry point → renders ChatInterface
└── components/
    └── ChatInterface.tsx     # Entire chat UI: personas, palette, avatars, chat logic
```

### Key design constants in `ChatInterface.tsx`

| Constant | Value | Why |
|---|---|---|
| `ANALYST_SVG` | Twemoji CDN URL for 🧐 | Cross-platform consistent emoji |
| `USER_SVG` | Twemoji CDN URL for 😰 | Cross-platform consistent emoji |
| `EMOJI_SCALE` | `109%` | `1 / (33/36)` — Twemoji face/viewBox ratio |

Avatars are loaded as `<img>` elements from the [Twemoji](https://github.com/twitter/twemoji) SVG CDN (jsDelivr, v14.0.2) rather than system emoji glyphs, so they look identical on every platform and browser.

## Color Palette

Four discrete steps — every touching surface pair is exactly ±1 step:

| Step | Hex | Surface |
|---|---|---|
| 1 | `#D45F2A` | Page background |
| 2 | `#EDA551` | Header, user chat bubbles, user avatar |
| 3 | `#F9D074` | Message area, send button |
| 4 | `#F8F0E4` | AI chat bubbles, input footer, textarea |
| Accent | `#E2C3DA` | Focus rings, decorative borders |

## Deploying to Vercel

The repo-level `vercel.json` handles routing for both the Next.js frontend and the Python backend. Just run `vercel` from the repo root and follow the prompts!
