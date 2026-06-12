"""API contract tests via FastAPI's TestClient — Anthropic client is faked."""

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(app_module):
    return TestClient(app_module.app, raise_server_exceptions=False)


@pytest.fixture
def fake_anthropic(app_module, monkeypatch):
    """Replace the Anthropic client; records the kwargs of the last call."""
    calls = {}

    class FakeMessages:
        def create(self, **kwargs):
            calls.update(kwargs)
            return SimpleNamespace(content=[SimpleNamespace(text="Ja. Zis is a reply.")])

    class FakeAnthropic:
        def __init__(self, api_key=None):
            calls["api_key"] = api_key
            self.messages = FakeMessages()

    monkeypatch.setattr(app_module.anthropic, "Anthropic", FakeAnthropic)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    # Keep retrieval out of contract tests — it has its own suite.
    monkeypatch.setattr(app_module, "_grounded_system_prompt", lambda q: app_module.SYSTEM_PROMPT)
    return calls


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_chat_round_trip(client, fake_anthropic):
    body = {"messages": [
        {"role": "assistant", "content": "Ah. You haff come."},
        {"role": "user", "content": "I had a strange dream."},
    ]}
    response = client.post("/api/chat", json=body)
    assert response.status_code == 200
    assert response.json() == {"reply": "Ja. Zis is a reply."}
    # Full history forwarded, system prompt attached.
    assert len(fake_anthropic["messages"]) == 2
    assert fake_anthropic["system"].startswith("You are a stern")


def test_chat_missing_key_is_clean_500(client, app_module, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(app_module, "_grounded_system_prompt", lambda q: app_module.SYSTEM_PROMPT)
    response = client.post("/api/chat", json={"messages": [{"role": "user", "content": "hi"}]})
    assert response.status_code == 500
    assert "ANTHROPIC_API_KEY" in response.json()["detail"]


def test_chat_rejects_malformed_body(client):
    assert client.post("/api/chat", json={"nope": True}).status_code == 422


def test_chat_final_flag_appends_closing_instruction(client, fake_anthropic):
    body = {
        "messages": [{"role": "user", "content": "I see. So that is it?"}],
        "final": True,
    }
    assert client.post("/api/chat", json=body).status_code == 200
    assert "end of the session" in fake_anthropic["system"].lower()


def test_chat_without_final_flag_is_unchanged(client, fake_anthropic):
    body = {"messages": [{"role": "user", "content": "hello"}]}
    assert client.post("/api/chat", json=body).status_code == 200
    assert "end of the session" not in fake_anthropic["system"].lower()


def test_health_reports_corpus_size(client, app_module):
    # Lets production confirm at a glance that the index was bundled and
    # loaded: 0 means the serverless function is running ungrounded.
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    assert body["corpus_chunks"] == len(app_module._CHUNKS)
    assert body["corpus_chunks"] > 0  # the committed index must load locally
