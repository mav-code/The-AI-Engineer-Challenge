# The Analyst — Backend API

FastAPI backend that powers The Analyst chat interface. Accepts a user message, passes it to OpenAI with the system prompt, and returns the reply. Deployed as a Python serverless function on Vercel.

## Prerequisites

- [`uv`](https://github.com/astral-sh/uv) package manager (`pip install uv`)
- `uv` provisions Python 3.12 automatically — no separate interpreter needed
- An OpenAI API key in the `OPENAI_API_KEY` environment variable

## Setup

All commands run from the **repository root**.

```bash
uv sync
```

This creates `.venv/` and fetches Python 3.12 if it isn't already available.

## Running the Server

```bash
export OPENAI_API_KEY=sk-your-key-here
uv run uvicorn api.index:app --reload
```

Server runs at `http://localhost:8000` with auto-reload. If port 8000 is already taken:

```bash
lsof -ti:8000 | xargs kill -9
```

## API Endpoints

### `POST /api/chat`

Send a user message, receive the analyst's reply.

**Request:**
```json
{ "message": "I've been feeling very anxious lately." }
```

**Response:**
```json
{ "reply": "Anxious. Yes. That is... expected. Tell me more about your mother." }
```

### `GET /api/health`
```json
{ "status": "ok" }
```

### `GET /`
```json
{ "status": "ok" }
```

## System Prompt

The backend currently uses the system prompt `"You are a supportive mental coach."` The frontend presents a stern psychoanalyst persona ("The Analyst"), but the backend system prompt has not yet been updated to match. Aligning them is a pending improvement.

## Interactive API Docs

With the server running:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing with curl

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I have been having troubling dreams."}'
```

## CORS

Configured to accept requests from any origin (`*`). Restrict in `index.py` for production if needed.
