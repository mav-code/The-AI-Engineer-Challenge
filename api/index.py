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
    "Keep responses concise."
)

class ChatRequest(BaseModel):
    message: str

@app.get("/")
def root():
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
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": request.message}],
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
        #         {"role": "user", "content": request.message},
        #     ],
        # )
        # reply = response.choices[0].message.content

        # ─────────────────────────────────────────────────────────────────────

        return {"reply": reply}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calling API: {str(e)}")
