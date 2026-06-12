"""Cost guards: history trimming, message caps, and per-IP rate limiting.

These keep a public POC endpoint from burning API credit: conversation
history is the only unbounded token cost, and the rate limit defeats
runaway scripts. Limits are set so a human conversing in good faith
never notices them.
"""

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def capture(app_module, monkeypatch):
    """Fake Anthropic client + clean rate-limit state; records call kwargs."""
    calls = {}

    class FakeAnthropic:
        def __init__(self, api_key=None):
            self.messages = SimpleNamespace(
                create=lambda **kw: (calls.update(kw), SimpleNamespace(
                    content=[SimpleNamespace(text="Hm.")]
                ))[1]
            )

    monkeypatch.setattr(app_module.anthropic, "Anthropic", FakeAnthropic)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(app_module, "_grounded_system_prompt", lambda q: app_module.SYSTEM_PROMPT)
    monkeypatch.setattr(app_module, "_RATE_BUCKETS", {})
    return calls


@pytest.fixture
def client(app_module):
    return TestClient(app_module.app, raise_server_exceptions=False)


def user(i):
    return {"role": "user", "content": f"message number {i}"}


def test_history_trimmed_to_most_recent(app_module, client, capture):
    body = {"messages": [user(i) for i in range(30)]}
    assert client.post("/api/chat", json=body).status_code == 200
    sent = capture["messages"]
    assert len(sent) == app_module.HISTORY_MAX_MESSAGES
    assert sent[-1]["content"] == "message number 29"  # newest kept
    assert sent[0]["content"] == f"message number {30 - app_module.HISTORY_MAX_MESSAGES}"


def test_oversized_message_truncated(app_module, client, capture):
    body = {"messages": [{"role": "user", "content": "x" * 50_000}]}
    assert client.post("/api/chat", json=body).status_code == 200
    assert len(capture["messages"][0]["content"]) == app_module.MESSAGE_MAX_CHARS


def test_rate_limit_kicks_in_and_stays_in_persona(app_module, client, capture):
    body = {"messages": [user(0)]}
    for _ in range(app_module.RATE_LIMIT_PER_MINUTE):
        assert client.post("/api/chat", json=body).status_code == 200
    response = client.post("/api/chat", json=body)
    assert response.status_code == 429
    assert "minute" in response.json()["detail"].lower()


def test_rate_limit_is_per_ip(app_module, client, capture):
    body = {"messages": [user(0)]}
    for _ in range(app_module.RATE_LIMIT_PER_MINUTE):
        client.post("/api/chat", json=body)
    assert client.post("/api/chat", json=body).status_code == 429
    # a different forwarded IP gets its own bucket
    other = client.post("/api/chat", json=body, headers={"x-forwarded-for": "203.0.113.7"})
    assert other.status_code == 200


def test_rate_limit_window_expires(app_module, client, capture, monkeypatch):
    body = {"messages": [user(0)]}
    for _ in range(app_module.RATE_LIMIT_PER_MINUTE):
        client.post("/api/chat", json=body)
    assert client.post("/api/chat", json=body).status_code == 429
    # fast-forward 61 seconds: bucket entries expire
    real_time = app_module.time.time()
    monkeypatch.setattr(app_module.time, "time", lambda: real_time + 61)
    assert client.post("/api/chat", json=body).status_code == 200
