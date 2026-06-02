# 🧠 Mental Coach – Frontend

A warm, orange-to-yellow chat interface for your AI-powered supportive mental coach. Built with **Next.js 14**, **TypeScript**, and **Tailwind CSS**.

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

Open [http://localhost:3000](http://localhost:3000) and start chatting!

> The frontend automatically proxies `/api/*` requests to port 8000 during development, so no extra config is needed.

## Project Structure

```
frontend/
├── app/
│   ├── globals.css       # Tailwind imports
│   ├── layout.tsx        # Root layout + metadata
│   └── page.tsx          # Entry point → renders ChatInterface
└── components/
    └── ChatInterface.tsx # The whole chat UI lives here
```

## Deploying to Vercel

The repo-level `vercel.json` handles routing for both the Next.js frontend and the Python backend. Just run `vercel` from the repo root and follow the prompts!
