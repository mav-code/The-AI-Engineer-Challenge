from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# ── PROVIDER IMPORT ── comment in one, comment out the other ──────────────────
import anthropic
# from openai import OpenAI
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
        # ── PROVIDER BLOCK ── comment in the block matching your import above ─

        # Anthropic
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=256,
            system=SYSTEM_PROMPT,
            messages=[{"role": m.role, "content": m.content} for m in request.messages],
        )
        reply = response.content[0].text

        # OpenAI
        # api_key = os.getenv("OPENAI_API_KEY")
        # if not api_key:
        #     raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")
        # client = OpenAI(api_key=api_key)
        # response = client.chat.completions.create(
        #     model="gpt-5",
        #     messages=[
        #         {"role": "system", "content": SYSTEM_PROMPT},
        #         *[{"role": m.role, "content": m.content} for m in request.messages],
        #     ],
        # )
        # reply = response.choices[0].message.content

        # ─────────────────────────────────────────────────────────────────────

        return {"reply": reply}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calling API: {str(e)}")
