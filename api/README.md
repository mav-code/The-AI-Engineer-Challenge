# The Analyst — Backend API

FastAPI backend that powers The Analyst chat interface. Accepts the conversation history, retrieves the most relevant passages from a precomputed index of public-domain psychoanalytic texts, injects them into the system prompt, passes everything to Claude, and returns the reply. Deployed as a Python serverless function on Vercel.

## Prerequisites

- [`uv`](https://github.com/astral-sh/uv) package manager (`pip install uv`)
- `uv` provisions Python 3.12 automatically — no separate interpreter needed
- An Anthropic API key in the `ANTHROPIC_API_KEY` environment variable (chat)
- An OpenAI API key in the `OPENAI_API_KEY` environment variable (query embeddings for retrieval — without it the chat still works, just ungrounded)

## Setup

All commands run from the **repository root**.

```bash
uv sync
```

This creates `.venv/` and fetches Python 3.12 if it isn't already available.

## Running the Server

```bash
export ANTHROPIC_API_KEY=sk-your-key-here
export OPENAI_API_KEY=sk-your-other-key-here
uv run uvicorn api.index:app --reload
```

Server runs at `http://localhost:8000` with auto-reload. If port 8000 is already taken:

```bash
lsof -ti:8000 | xargs kill -9
```

## API Endpoints

### `POST /api/chat`

Send the conversation history, receive the analyst's reply. The latest user message doubles as the retrieval query: its embedding is compared against `api/_index/embeddings.npy` and the top-4 passages are injected into the system prompt as grounding (see `scripts/build_index.py` for how the index is built).

**Request:**
```json
{
  "messages": [
    { "role": "assistant", "content": "Ah. You haff come." },
    { "role": "user", "content": "I've been feeling very anxious lately." }
  ]
}
```

**Response:**
```json
{ "reply": "Anxious. Yes. That is... expected. Tell me more about your mother." }
```

The body also accepts an optional `"final": true` flag — the frontend sends it on a session's twelfth user turn, and the system prompt gains a closing instruction so the Analyst delivers a final pronouncement and dismisses the patient.

### `POST /api/notes`

The Analyst's private case file on a concluded session. Send the same `messages` shape; receive `{ "notes": "Case notes — …" }`. No retrieval, capped at 400 output tokens; the frontend gates it behind session end so it costs at most one extra call per session.

### Guards (both POST endpoints)

History is trimmed server-side to the last 20 messages, each message is capped at 2,000 characters, and requests are limited to 15/minute per IP (HTTP 429 with a politely menacing detail message).

### `GET /api/health`
```json
{ "status": "ok" }
```

### `GET /`
```json
{ "status": "ok" }
```

## Interactive API Docs

With the server running:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing with curl

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "I have been having troubling dreams."}]}'
```

## CORS

Configured to accept requests from any origin (`*`). Restrict in `index.py` for production if needed.
