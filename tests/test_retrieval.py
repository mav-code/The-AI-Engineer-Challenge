"""Runtime retrieval logic: cosine top-k, prompt assembly, graceful fallbacks.

Uses the fake_index fixture (synthetic 6x8 matrix) and a stubbed
_embed_query — no network, no keys.
"""

import numpy as np


def query_toward(matrix, *weighted_rows):
    """Build a query vector as a weighted sum of index rows."""
    vector = np.zeros(matrix.shape[1], dtype=np.float32)
    for row, weight in weighted_rows:
        vector += weight * matrix[row]
    return vector


def test_top1_is_most_similar_chunk(app_module, fake_index, monkeypatch):
    matrix, _ = fake_index
    monkeypatch.setattr(app_module, "_embed_query", lambda text: query_toward(matrix, (2, 5.0), (5, 2.0)))
    results = app_module._retrieve("anything")
    assert results[0]["source"] == "S2"


def test_returns_at_most_k(app_module, fake_index, monkeypatch):
    matrix, _ = fake_index
    monkeypatch.setattr(app_module, "_embed_query", lambda text: query_toward(matrix, (0, 1.0)))
    assert len(app_module._retrieve("anything", k=4)) <= 4


def test_grounded_prompt_keeps_persona_first(app_module, fake_index, monkeypatch):
    matrix, _ = fake_index
    monkeypatch.setattr(app_module, "_embed_query", lambda text: query_toward(matrix, (2, 1.0)))
    prompt = app_module._grounded_system_prompt("anything")
    assert prompt.startswith(app_module.SYSTEM_PROMPT)
    assert "Draw on these passages where relevant" in prompt
    assert "[S2]" in prompt


def test_empty_query_is_ungrounded(app_module, fake_index):
    assert app_module._grounded_system_prompt("   ") == app_module.SYSTEM_PROMPT


def test_missing_index_is_ungrounded(app_module, monkeypatch):
    monkeypatch.setattr(app_module, "_EMBEDDINGS", None)
    monkeypatch.setattr(app_module, "_CHUNKS", [])
    assert app_module._grounded_system_prompt("my mother") == app_module.SYSTEM_PROMPT


def test_embed_failure_falls_back_to_ungrounded(app_module, fake_index, monkeypatch):
    def boom(text):
        raise RuntimeError("embedding api down")

    monkeypatch.setattr(app_module, "_embed_query", boom)
    assert app_module._grounded_system_prompt("my mother") == app_module.SYSTEM_PROMPT


def test_dim_mismatch_falls_back_to_ungrounded(app_module, fake_index, monkeypatch):
    monkeypatch.setattr(app_module, "_embed_query", lambda text: np.ones(3, dtype=np.float32))
    assert app_module._grounded_system_prompt("my mother") == app_module.SYSTEM_PROMPT


def test_committed_index_is_consistent(app_module):
    """Integration check against the real committed artifacts."""
    assert app_module._EMBEDDINGS is not None, "committed index failed to load"
    assert app_module._EMBEDDINGS.shape[0] == len(app_module._CHUNKS)
    norms = np.linalg.norm(app_module._EMBEDDINGS[:32], axis=1)
    assert np.allclose(norms, 1.0, atol=0.01), "index rows must be pre-normalized"
