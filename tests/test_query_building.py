"""Context-aware retrieval queries and the similarity floor.

The retrieval query is built from the latest user message PLUS the preceding
assistant reply, so follow-ups like "what does that mean?" inherit their
context. The floor drops passages whose cosine similarity is too weak to be
real grounding (off-topic questions retrieve nothing instead of noise).
"""

import numpy as np
import pytest


def msgs(app_module, *pairs):
    return [app_module.Message(role=r, content=c) for r, c in pairs]


# ── query building ────────────────────────────────────────────────────────────

def test_query_includes_previous_assistant_turn(app_module):
    messages = msgs(
        app_module,
        ("assistant", "Ze dream of teeth is a classic castration anxiety."),
        ("user", "What does that mean?"),
    )
    query = app_module._retrieval_query(messages)
    assert "castration anxiety" in query
    assert query.endswith("What does that mean?")


def test_query_is_just_user_text_without_assistant(app_module):
    messages = msgs(app_module, ("user", "I keep dreaming of falling."))
    assert app_module._retrieval_query(messages) == "I keep dreaming of falling."


def test_query_caps_length_but_keeps_latest_user_text(app_module):
    messages = msgs(
        app_module,
        ("assistant", "blah " * 2000),  # ~10,000 chars of context
        ("user", "the tail marker"),
    )
    query = app_module._retrieval_query(messages)
    assert len(query) <= app_module.QUERY_MAX_CHARS
    assert query.endswith("the tail marker")


def test_query_empty_messages(app_module):
    assert app_module._retrieval_query([]) == ""


# ── similarity floor ──────────────────────────────────────────────────────────

@pytest.fixture
def orthonormal_index(app_module, monkeypatch):
    """6 chunks embedded as the first 6 standard basis vectors of R^8 —
    cosine scores are then exactly the query's coordinates."""
    matrix = np.eye(6, 8, dtype=np.float32)
    chunks = [{"source": f"S{i}", "text": f"chunk text {i}"} for i in range(6)]
    monkeypatch.setattr(app_module, "_EMBEDDINGS", matrix)
    monkeypatch.setattr(app_module, "_CHUNKS", chunks)
    monkeypatch.setattr(app_module, "_EMBED_MODEL", "stub-model")
    return matrix


def test_floor_keeps_only_strong_matches(app_module, orthonormal_index, monkeypatch):
    # similarity 1.0 to S2, ~0 to everything else
    query = np.zeros(8, dtype=np.float32)
    query[2] = 1.0
    monkeypatch.setattr(app_module, "_embed_query", lambda text: query)
    results = app_module._retrieve("on-topic question")
    assert [r["source"] for r in results] == ["S2"]


def test_floor_returns_nothing_for_off_topic_query(app_module, orthonormal_index, monkeypatch):
    # orthogonal to every indexed chunk: all similarities are 0
    query = np.zeros(8, dtype=np.float32)
    query[7] = 1.0
    monkeypatch.setattr(app_module, "_embed_query", lambda text: query)
    assert app_module._retrieve("how do I configure DNS on Vercel?") == []
    assert app_module._grounded_system_prompt("how do I configure DNS?") == app_module.SYSTEM_PROMPT


def test_floor_is_a_sane_cosine_value(app_module):
    assert 0.0 < app_module.MIN_SIMILARITY < 1.0


# ── chat() wiring ─────────────────────────────────────────────────────────────

def test_chat_builds_query_from_context(app_module, monkeypatch):
    from fastapi.testclient import TestClient
    from types import SimpleNamespace

    captured = {}

    def recording_prompt(query):
        captured["query"] = query
        return app_module.SYSTEM_PROMPT

    class FakeAnthropic:
        def __init__(self, api_key=None):
            self.messages = SimpleNamespace(
                create=lambda **kw: SimpleNamespace(content=[SimpleNamespace(text="Hm.")])
            )

    monkeypatch.setattr(app_module, "_grounded_system_prompt", recording_prompt)
    monkeypatch.setattr(app_module.anthropic, "Anthropic", FakeAnthropic)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    client = TestClient(app_module.app)
    client.post("/api/chat", json={"messages": [
        {"role": "user", "content": "I dreamt my teeth fell out."},
        {"role": "assistant", "content": "Teeth, ja. Ze loss of potency."},
        {"role": "user", "content": "Why would I dream that?"},
    ]})
    assert "Ze loss of potency" in captured["query"]
    assert captured["query"].endswith("Why would I dream that?")
