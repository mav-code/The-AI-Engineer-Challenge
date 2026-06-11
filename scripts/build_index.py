"""Build the retrieval index for The Analyst.

Pipeline: fetch -> chunk -> embed -> write.

  1. fetch  - download public-domain psychoanalytic texts from Project
              Gutenberg into data/texts/ (skipped if already present).
  2. chunk  - strip Gutenberg boilerplate, split into paragraphs, pack
              paragraphs into ~300-500-token windows with one paragraph
              of overlap between consecutive windows.
  3. embed  - embed every chunk with the same model the runtime uses for
              queries (see EMBEDDING PROVIDER toggle below).
  4. write  - api/_index/embeddings.npy   (float16, row-normalized)
              api/_index/chunks.json      (model name, dims, chunk texts + sources)

The artifacts live under api/_index/ (not data/) so Vercel bundles them
with the serverless function. Re-run any time with:

    OPENAI_API_KEY=sk-... uv run python scripts/build_index.py

The script is idempotent: cached downloads are reused, and the index is
rewritten from scratch on every run.
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

import numpy as np

# ── EMBEDDING PROVIDER IMPORT ── comment in one, comment out the other ───────
# (must match the toggle in api/index.py — corpus and query embeddings have to
# come from the same model or cosine similarity is meaningless)
from openai import OpenAI
# import voyageai
# ─────────────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent
TEXTS_DIR = REPO_ROOT / "data" / "texts"
INDEX_DIR = REPO_ROOT / "api" / "_index"

# All four are pre-1929 public-domain translations (Eder, Brill, Hall, Hinkle).
# Deliberately NOT the Strachey Standard Edition, which is still in copyright.
BOOKS = [
    {
        "file": "freud_dream_psychology.txt",
        "url": "https://www.gutenberg.org/cache/epub/15489/pg15489.txt",
        "source": "Freud, Dream Psychology (trans. Eder)",
    },
    {
        "file": "freud_three_contributions.txt",
        "url": "https://www.gutenberg.org/cache/epub/14969/pg14969.txt",
        "source": "Freud, Three Contributions to the Theory of Sex (trans. Brill)",
    },
    {
        "file": "freud_general_introduction.txt",
        "url": "https://www.gutenberg.org/cache/epub/38219/pg38219.txt",
        "source": "Freud, A General Introduction to Psychoanalysis (trans. Hall)",
    },
    {
        "file": "jung_psychology_of_the_unconscious.txt",
        "url": "https://www.gutenberg.org/cache/epub/65903/pg65903.txt",
        "source": "Jung, Psychology of the Unconscious (trans. Hinkle)",
    },
]

# Window sizing. Token counts are estimated as words / 0.75 (the usual
# ~4-chars-per-token heuristic); exact counts don't matter for chunking.
TARGET_TOKENS = 400   # aim for the middle of the 300-500 spec
MAX_TOKENS = 500
MIN_PARAGRAPH_WORDS = 5  # drop page numbers, lone headings, etc.


def est_tokens(text: str) -> int:
    return int(len(text.split()) / 0.75)


def fetch() -> None:
    TEXTS_DIR.mkdir(parents=True, exist_ok=True)
    for book in BOOKS:
        dest = TEXTS_DIR / book["file"]
        if dest.exists():
            print(f"  cached  {book['file']}")
            continue
        print(f"  fetch   {book['url']}")
        with urllib.request.urlopen(book["url"]) as resp:
            dest.write_bytes(resp.read())


def strip_gutenberg_boilerplate(raw: str) -> str:
    """Keep only the text between the *** START/END OF ... *** markers."""
    start = re.search(r"\*\*\* ?START OF.*?\*\*\*", raw)
    end = re.search(r"\*\*\* ?END OF.*?\*\*\*", raw)
    if not (start and end):
        raise ValueError("Gutenberg START/END markers not found")
    return raw[start.end():end.start()]


def split_paragraphs(text: str) -> list[str]:
    paragraphs = []
    for block in re.split(r"\n\s*\n", text):
        para = " ".join(block.split())  # collapse internal newlines/whitespace
        if len(para.split()) >= MIN_PARAGRAPH_WORDS:
            paragraphs.append(para)
    return paragraphs


def split_oversized(para: str) -> list[str]:
    """Sentence-split the rare paragraph that alone exceeds MAX_TOKENS."""
    if est_tokens(para) <= MAX_TOKENS:
        return [para]
    sentences = re.split(r"(?<=[.!?])\s+", para)
    pieces, current = [], ""
    for sentence in sentences:
        candidate = f"{current} {sentence}".strip()
        if current and est_tokens(candidate) > MAX_TOKENS:
            pieces.append(current)
            current = sentence
        else:
            current = candidate
    if current:
        pieces.append(current)
    return pieces


def chunk_book(text: str, source: str) -> list[dict]:
    """Pack paragraphs into ~TARGET_TOKENS windows, overlapping by one
    paragraph so a thought split across a window boundary still appears
    whole in one of the two chunks."""
    paragraphs = [p for para in split_paragraphs(text) for p in split_oversized(para)]
    chunks, window = [], []

    for para in paragraphs:
        if window and est_tokens(" ".join(window)) + est_tokens(para) > TARGET_TOKENS:
            chunks.append({"source": source, "text": "\n\n".join(window)})
            overlap = window[-1]  # one-paragraph overlap with the next window —
            # but only if it leaves room under the hard cap
            if est_tokens(overlap) + est_tokens(para) <= MAX_TOKENS:
                window = [overlap, para]
            else:
                window = [para]
        else:
            window.append(para)
    if window:
        chunks.append({"source": source, "text": "\n\n".join(window)})
    return chunks


def embed(texts: list[str]) -> tuple[np.ndarray, str]:
    """Embed all chunks in batches. Returns (matrix, model_name)."""

    # ── EMBEDDING PROVIDER BLOCK ── comment in the block matching your import ─

    # OpenAI
    model = "text-embedding-3-small"
    client = OpenAI()  # reads OPENAI_API_KEY from the environment
    vectors = []
    for i in range(0, len(texts), 128):
        batch = texts[i : i + 128]
        response = client.embeddings.create(model=model, input=batch)
        vectors.extend(item.embedding for item in response.data)
        print(f"  embedded {min(i + 128, len(texts))}/{len(texts)}")

    # Voyage
    # model = "voyage-3.5-lite"
    # client = voyageai.Client()  # reads VOYAGE_API_KEY from the environment
    # vectors = []
    # for i in range(0, len(texts), 128):
    #     batch = texts[i : i + 128]
    #     response = client.embed(batch, model=model, input_type="document")
    #     vectors.extend(response.embeddings)
    #     print(f"  embedded {min(i + 128, len(texts))}/{len(texts)}")

    # ──────────────────────────────────────────────────────────────────────────

    return np.array(vectors, dtype=np.float32), model


def main() -> None:
    print("fetch:")
    fetch()

    print("chunk:")
    chunks = []
    for book in BOOKS:
        raw = (TEXTS_DIR / book["file"]).read_text(encoding="utf-8")
        book_chunks = chunk_book(strip_gutenberg_boilerplate(raw), book["source"])
        print(f"  {len(book_chunks):4d} chunks  {book['source']}")
        chunks.extend(book_chunks)
    print(f"  {len(chunks):4d} chunks total")

    if "--chunks-only" in sys.argv:
        print("(--chunks-only: skipping embed + write)")
        return

    print("embed:")
    matrix, model = embed([c["text"] for c in chunks])

    # Pre-normalize rows so runtime cosine similarity is a plain dot product.
    matrix /= np.linalg.norm(matrix, axis=1, keepdims=True)

    print("write:")
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    # float16 halves the committed file size; cosine ranking is insensitive
    # to the precision loss. The runtime upcasts back to float32.
    np.save(INDEX_DIR / "embeddings.npy", matrix.astype(np.float16))
    (INDEX_DIR / "chunks.json").write_text(
        json.dumps({"model": model, "dims": int(matrix.shape[1]), "chunks": chunks}),
        encoding="utf-8",
    )
    print(f"  {INDEX_DIR / 'embeddings.npy'}  {matrix.shape}")
    print(f"  {INDEX_DIR / 'chunks.json'}")


if __name__ == "__main__":
    main()
