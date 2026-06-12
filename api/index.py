import json
import os
import time
from collections import deque
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── PROVIDER IMPORT (chat) ── comment in one, comment out the other ──────────
import anthropic
# from openai import OpenAI as OpenAIChat
# ─────────────────────────────────────────────────────────────────────────────

# ── EMBEDDING PROVIDER IMPORT ── comment in one, comment out the other ───────
# (must match scripts/build_index.py — corpus and query embeddings have to
# come from the same model or cosine similarity is meaningless)
from openai import OpenAI as OpenAIEmbed
# import voyageai
# ─────────────────────────────────────────────────────────────────────────────

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SYSTEM_PROMPT = (
    "You are a stern, exacting continental psychoanalyst. "
    "You do not offer comfort — you offer analysis. "
    "Respond with clinical precision and probing questions. "
    "Keep every response to 1–3 sentences. "
    "Write in plain prose. Do not use markdown, bullet points, bold, or headers. "
    "You may use *asterisks* around a word to italicize it for emphasis."
    "You can use unorthodox spelling to imitate something like an Austrian accent, to enhance the effect. But don't degrade comprehensibility too much."
)

# Appended to the system prompt when retrieval succeeds. Framed so the
# grounding deepens the analysis without breaking persona or format rules.
GROUNDING_PREAMBLE = (
    "\n\nBelow are passages from your library — Freud and Jung in the early "
    "translations you studied. Draw on these passages where relevant: let "
    "their concepts sharpen your analysis. They are your own learned knowledge; "
    "never mention passages, excerpts, sources, or that you were given text. "
    "Every rule above still binds you — above all the 1–3 sentence limit.\n"
)

# ── Retrieval index ───────────────────────────────────────────────────────────
# Built offline by scripts/build_index.py and committed, so the serverless
# function only ever embeds the query (one API call) — no model weights, no
# vector database. Loaded once at module load, not per request.
_INDEX_DIR = Path(__file__).parent / "_index"
try:
    # float16 on disk (half the repo weight); float32 in memory for the dot product.
    _EMBEDDINGS = np.load(_INDEX_DIR / "embeddings.npy").astype(np.float32)
    _meta = json.loads((_INDEX_DIR / "chunks.json").read_text(encoding="utf-8"))
    _EMBED_MODEL = _meta["model"]
    _CHUNKS = _meta["chunks"]
    assert _EMBEDDINGS.shape[1] == _meta["dims"], "index dims mismatch"
    assert _EMBEDDINGS.shape[0] == len(_CHUNKS), "embeddings/chunks count mismatch"
except FileNotFoundError:
    # No index built (or not bundled) — the analyst improvises without grounding.
    _EMBEDDINGS, _CHUNKS, _EMBED_MODEL = None, [], None


def _embed_query(text: str) -> np.ndarray:
    """Embed one query with the SAME model used to build the corpus."""

    # ── EMBEDDING PROVIDER BLOCK ── comment in the block matching your import ─

    # OpenAI
    client = OpenAIEmbed()  # reads OPENAI_API_KEY from the environment
    response = client.embeddings.create(model=_EMBED_MODEL, input=[text])
    vector = np.array(response.data[0].embedding, dtype=np.float32)

    # Voyage
    # client = voyageai.Client()  # reads VOYAGE_API_KEY from the environment
    # response = client.embed([text], model=_EMBED_MODEL, input_type="query")
    # vector = np.array(response.embeddings[0], dtype=np.float32)

    # ──────────────────────────────────────────────────────────────────────────

    assert vector.shape[0] == _EMBEDDINGS.shape[1], (
        f"query dims {vector.shape[0]} != corpus dims {_EMBEDDINGS.shape[1]} — "
        "query and corpus must use the same embedding model"
    )
    return vector


# Passages scoring below this cosine similarity are noise, not grounding —
# an off-topic question ("how do I fix my DNS?") should retrieve nothing
# rather than four irrelevant pages of libido theory. Tuned by eye for
# text-embedding-3-small; log scores temporarily if re-tuning.
MIN_SIMILARITY = 0.30

# Retrieval queries are capped to keep the embedding input bounded; truncation
# drops the OLDEST text so the latest user message always survives intact.
QUERY_MAX_CHARS = 2000


def _retrieval_query(messages: list["Message"]) -> str:
    """Latest user message plus the assistant reply before it, so follow-ups
    like "what does that mean?" carry their context into retrieval."""
    latest_user = next((m.content for m in reversed(messages) if m.role == "user"), "")
    last_assistant = next((m.content for m in reversed(messages) if m.role == "assistant"), "")
    query = f"{last_assistant}\n{latest_user}".strip() if last_assistant else latest_user
    return query[-QUERY_MAX_CHARS:]


def _retrieve(query: str, k: int = 4) -> list[dict]:
    """Top-k chunks by cosine similarity (rows are pre-normalized, so a
    normalized-query dot product IS cosine similarity), filtered by
    MIN_SIMILARITY. Returns [] on any failure so a retrieval hiccup never
    takes down the chat itself."""
    if _EMBEDDINGS is None or not query.strip():
        return []
    try:
        vector = _embed_query(query)
        vector /= np.linalg.norm(vector)
        scores = _EMBEDDINGS @ vector
        top = np.argpartition(scores, -k)[-k:]
        top = top[np.argsort(scores[top])[::-1]]
        return [_CHUNKS[i] for i in top if scores[i] >= MIN_SIMILARITY]
    except Exception as exc:  # noqa: BLE001 — degrade to ungrounded, don't 500
        print(f"retrieval failed, continuing ungrounded: {exc}")
        return []


def _grounded_system_prompt(query: str) -> str:
    passages = _retrieve(query)
    if not passages:
        return SYSTEM_PROMPT
    rendered = "\n\n".join(f"[{p['source']}]\n{p['text']}" for p in passages)
    return SYSTEM_PROMPT + GROUNDING_PREAMBLE + "\n" + rendered
# ──────────────────────────────────────────────────────────────────────────────


# ── Cost guards ───────────────────────────────────────────────────────────────
# Conversation history is the only unbounded token cost in the app, and this
# is a public endpoint spending real credit. Limits are sized so a human
# conversing in good faith never hits them.
HISTORY_MAX_MESSAGES = 20   # only the most recent messages reach the model
MESSAGE_MAX_CHARS = 2000    # per-message cap (silently truncated)
RATE_LIMIT_PER_MINUTE = 15  # per IP — defeats scripts, invisible to humans

# Per-IP request timestamps. Module state is per serverless instance, so this
# is best-effort rather than airtight — fine for a POC; instances are
# short-lived enough that the dict never grows meaningfully.
_RATE_BUCKETS: dict[str, deque] = {}


def _client_ip(raw_request: Request) -> str:
    forwarded = raw_request.headers.get("x-forwarded-for")  # set by Vercel
    if forwarded:
        return forwarded.split(",")[0].strip()
    return raw_request.client.host if raw_request.client else "unknown"


def _rate_limited(ip: str) -> bool:
    """Sliding 60-second window per IP."""
    now = time.time()
    bucket = _RATE_BUCKETS.setdefault(ip, deque())
    while bucket and now - bucket[0] > 60:
        bucket.popleft()
    if len(bucket) >= RATE_LIMIT_PER_MINUTE:
        return True
    bucket.append(now)
    return False
# ──────────────────────────────────────────────────────────────────────────────


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/chat")
def chat(request: ChatRequest, raw_request: Request):
    if _rate_limited(_client_ip(raw_request)):
        raise HTTPException(
            status_code=429,
            detail="Enough. Ve are not having a crisis. Breathe, und try again in a minute.",
        )

    # Trim history and cap message sizes BEFORE anything touches a paid API.
    messages = [
        Message(role=m.role, content=m.content[:MESSAGE_MAX_CHARS])
        for m in request.messages[-HISTORY_MAX_MESSAGES:]
    ]

    try:
        # Ground the reply in the latest exchange (the retrieval key).
        system_prompt = _grounded_system_prompt(_retrieval_query(messages))

        # ── PROVIDER BLOCK (chat) ── comment in the block matching your import ─

        # Anthropic
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=256,
            system=system_prompt,
            messages=[{"role": m.role, "content": m.content} for m in messages],
        )
        reply = response.content[0].text

        # OpenAI
        # api_key = os.getenv("OPENAI_API_KEY")
        # if not api_key:
        #     raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")
        # client = OpenAIChat(api_key=api_key)
        # response = client.chat.completions.create(
        #     model="gpt-5",
        #     messages=[
        #         {"role": "system", "content": system_prompt},
        #         *[{"role": m.role, "content": m.content} for m in messages],
        #     ],
        # )
        # reply = response.choices[0].message.content

        # ───────────────────────────────────────────────────────────────────────

        return {"reply": reply}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calling API: {str(e)}")
