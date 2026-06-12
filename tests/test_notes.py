"""POST /api/notes — the Analyst's case file on a concluded session.

One extra Haiku call per session, user-initiated and gated behind session
end in the UI. No retrieval (the notes summarize the conversation; grounding
would add cost and nothing else).
"""

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(app_module):
    return TestClient(app_module.app, raise_server_exceptions=False)


@pytest.fixture
def capture(app_module, monkeypatch):
    calls = {}

    class FakeAnthropic:
        def __init__(self, api_key=None):
            self.messages = SimpleNamespace(
                create=lambda **kw: (calls.update(kw), SimpleNamespace(
                    content=[SimpleNamespace(text="Case notes — ze patient resists.")]
                ))[1]
            )

    monkeypatch.setattr(app_module.anthropic, "Anthropic", FakeAnthropic)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(app_module, "_RATE_BUCKETS", {})
    return calls


TRANSCRIPT = {"messages": [
    {"role": "assistant", "content": "Ah. You haff come."},
    {"role": "user", "content": "I dreamt my teeth fell out."},
    {"role": "assistant", "content": "Zis is classic. Ve are done for today."},
]}


def test_notes_round_trip(client, capture):
    response = client.post("/api/notes", json=TRANSCRIPT)
    assert response.status_code == 200
    assert response.json() == {"notes": "Case notes — ze patient resists."}


def test_notes_use_case_file_prompt_not_chat_prompt(app_module, client, capture):
    client.post("/api/notes", json=TRANSCRIPT)
    assert "case notes" in capture["system"].lower()
    assert capture["system"] != app_module.SYSTEM_PROMPT


def test_notes_get_their_own_token_budget(app_module, client, capture):
    client.post("/api/notes", json=TRANSCRIPT)
    assert capture["max_tokens"] == app_module.NOTES_MAX_TOKENS
    assert capture["max_tokens"] > 256  # roomier than chat replies


def test_notes_transcript_ends_with_a_user_turn(client, capture):
    # The conversation ends on an assistant turn; the request to the model
    # must not (assistant-final messages are prefill, banned on newer models).
    client.post("/api/notes", json=TRANSCRIPT)
    assert capture["messages"][-1]["role"] == "user"


def test_notes_history_is_trimmed(app_module, client, capture):
    long = {"messages": [{"role": "user", "content": f"m{i}"} for i in range(40)]}
    client.post("/api/notes", json=long)
    # trimmed transcript + the appended write-your-notes user turn
    assert len(capture["messages"]) <= app_module.HISTORY_MAX_MESSAGES + 1


def test_notes_share_the_rate_limit(app_module, client, capture):
    for _ in range(app_module.RATE_LIMIT_PER_MINUTE):
        assert client.post("/api/notes", json=TRANSCRIPT).status_code == 200
    assert client.post("/api/notes", json=TRANSCRIPT).status_code == 429


def test_notes_missing_key_is_clean_500(client, app_module, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(app_module, "_RATE_BUCKETS", {})
    response = client.post("/api/notes", json=TRANSCRIPT)
    assert response.status_code == 500
    assert "ANTHROPIC_API_KEY" in response.json()["detail"]
