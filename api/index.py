import json
import os
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
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


def _retrieve(query: str, k: int = 4) -> list[dict]:
    """Top-k chunks by cosine similarity (rows are pre-normalized, so a
    normalized-query dot product IS cosine similarity). Returns [] on any
    failure so a retrieval hiccup never takes down the chat itself."""
    if _EMBEDDINGS is None or not query.strip():
        return []
    try:
        vector = _embed_query(query)
        vector /= np.linalg.norm(vector)
        scores = _EMBEDDINGS @ vector
        top = np.argpartition(scores, -k)[-k:]
        top = top[np.argsort(scores[top])[::-1]]
        return [_CHUNKS[i] for i in top]
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
def chat(request: ChatRequest):
    try:
        # Ground the reply in the latest user message (the retrieval key).
        latest_user = next(
            (m.content for m in reversed(request.messages) if m.role == "user"), ""
        )
        system_prompt = _grounded_system_prompt(latest_user)

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
            messages=[{"role": m.role, "content": m.content} for m in request.messages],
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
        #         *[{"role": m.role, "content": m.content} for m in request.messages],
        #     ],
        # )
        # reply = response.choices[0].message.content

        # ───────────────────────────────────────────────────────────────────────

        return {"reply": reply}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calling API: {str(e)}")
