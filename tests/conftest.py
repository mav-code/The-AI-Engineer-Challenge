"""Shared test setup.

All tests are keyless and networkless: external clients (Anthropic, OpenAI)
are monkeypatched, and retrieval is exercised against tiny synthetic indexes.
The committed real index and corpus texts are only ever *read*.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
# api/index.py and scripts/build_index.py are top-level modules, not packages.
sys.path.insert(0, str(REPO_ROOT / "api"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))


@pytest.fixture
def app_module():
    import index
    return index


@pytest.fixture
def fake_index(app_module, monkeypatch):
    """Replace the loaded index with a small deterministic one.

    Rows are an orthonormal-ish random basis (normalized), so tests can craft
    queries with exact known similarities.
    """
    rng = np.random.default_rng(0)
    matrix = rng.normal(size=(6, 8)).astype(np.float32)
    matrix /= np.linalg.norm(matrix, axis=1, keepdims=True)
    chunks = [{"source": f"S{i}", "text": f"chunk text {i}"} for i in range(6)]
    monkeypatch.setattr(app_module, "_EMBEDDINGS", matrix)
    monkeypatch.setattr(app_module, "_CHUNKS", chunks)
    monkeypatch.setattr(app_module, "_EMBED_MODEL", "stub-model")
    return matrix, chunks
