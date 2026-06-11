"""Build the retrieval index for The Analyst.

Pipeline: fetch -> chunk -> embed -> write.

  1. fetch  - download public-domain psychoanalytic texts from Project
              Gutenberg into data/texts/ (skipped if already present).
  2. chunk  - strip Gutenberg boilerplate AND non-content front/back matter
              (title pages, TOCs, translator boilerplate, indices — see the
              per-book "start"/"end" markers in BOOKS), split into
              paragraphs, pack paragraphs into ~300-500-token windows with
              one paragraph of overlap between consecutive windows.
  3. embed  - embed every chunk with the same model the runtime uses for
              queries (see EMBEDDING PROVIDER toggle below). Batches are
              token-budgeted and paced to stay under the OpenAI free-tier
              40K tokens-per-minute limit (see TPM_LIMIT).
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
import time
import urllib.request
from pathlib import Path

import numpy as np

# ── EMBEDDING PROVIDER IMPORT ── comment in one, comment out the other ───────
# (must match the toggle in api/index.py — corpus and query embeddings have to
# come from the same model or cosine similarity is meaningless)
from openai import OpenAI, RateLimitError
# import voyageai
# ─────────────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent
TEXTS_DIR = REPO_ROOT / "data" / "texts"
INDEX_DIR = REPO_ROOT / "api" / "_index"

# All four are pre-1929 public-domain translations (Eder, Brill, Hall, Hinkle).
# Deliberately NOT the Strachey Standard Edition, which is still in copyright.
#
# "start" / "end" prune non-content front and back matter so we don't pay to
# embed it. "start" is a unique opening phrase of the real content — cutting
# title pages, TOCs and translator boilerplate, but keeping substantive prose
# such as author prefaces and Hinkle's analytical introduction. "end"
# (optional) is the heading that opens pure back matter (the index); from it
# onward everything is dropped.
BOOKS = [
    {
        "file": "freud_dream_psychology.txt",
        "url": "https://www.gutenberg.org/cache/epub/15489/pg15489.txt",
        "source": "Freud, Dream Psychology (trans. Eder)",
        "start": r'In what we may term "prescientific days"',  # Chapter I
        "end": None,  # book runs straight into the Gutenberg license
    },
    {
        "file": "freud_three_contributions.txt",
        "url": "https://www.gutenberg.org/cache/epub/14969/pg14969.txt",
        "source": "Freud, Three Contributions to the Theory of Sex (trans. Brill)",
        "start": r"Although the author is fully aware of the gaps",  # Freud's own preface
        "end": r"^INDEX\s*$",
    },
    {
        "file": "freud_general_introduction.txt",
        "url": "https://www.gutenberg.org/cache/epub/38219/pg38219.txt",
        "source": "Freud, A General Introduction to Psychoanalysis (trans. Hall)",
        "start": r"I do not know how familiar some of you may be",  # First Lecture
        "end": None,  # endnotes are substantive; book then runs into the license
    },
    {
        "file": "jung_psychology_of_the_unconscious.txt",
        "url": "https://www.gutenberg.org/cache/epub/65903/pg65903.txt",
        "source": "Jung, Psychology of the Unconscious (trans. Hinkle)",
        "start": r"When Professor Freud of Vienna made his early discoveries",  # Hinkle's intro
        "end": r"^\s*INDEX\s*$",
    },
]

# Window sizing. Token counts are estimated as words / 0.75 (the usual
# ~4-chars-per-token heuristic); exact counts don't matter for chunking.
TARGET_TOKENS = 400   # aim for the middle of the 300-500 spec
MAX_TOKENS = 500
MIN_PARAGRAPH_WORDS = 5  # drop page numbers, lone headings, etc.

# Embedding-request pacing. The OpenAI free tier allows 40K tokens/minute for
# text-embedding-3-small; we keep each request comfortably below that (the
# word-count estimate undershoots the real tokenizer a bit) and sleep between
# requests so consecutive batches don't sum past the per-minute limit.
# On a paid tier you can raise TPM_LIMIT to your account's limit.
TPM_LIMIT = 40_000
BATCH_TOKEN_BUDGET = 25_000
MAX_RETRIES = 5


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


def prune_front_back_matter(text: str, book: dict) -> str:
    """Drop title pages, TOCs, translator boilerplate and trailing indices,
    keeping only the work itself (per-book markers defined in BOOKS)."""
    match = re.search(book["start"], text)
    if not match:
        raise ValueError(f"start marker not found in {book['file']}")
    text = text[match.start():]
    if book["end"]:
        match = re.search(book["end"], text, re.MULTILINE)
        if not match:
            raise ValueError(f"end marker not found in {book['file']}")
        text = text[: match.start()]
    return text


def token_budgeted_batches(texts: list[str]) -> list[list[str]]:
    """Group chunks into batches whose estimated token sum stays under
    BATCH_TOKEN_BUDGET, so no single request can blow the TPM limit."""
    batches, batch, budget = [], [], 0
    for text in texts:
        tokens = est_tokens(text)
        if batch and budget + tokens > BATCH_TOKEN_BUDGET:
            batches.append(batch)
            batch, budget = [], 0
        batch.append(text)
        budget += tokens
    if batch:
        batches.append(batch)
    return batches


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
    """Embed all chunks in token-budgeted, TPM-paced batches.
    Returns (matrix, model_name)."""
    batches = token_budgeted_batches(texts)

    # ── EMBEDDING PROVIDER BLOCK ── comment in the block matching your import ─

    # OpenAI
    model = "text-embedding-3-small"
    client = OpenAI()  # reads OPENAI_API_KEY from the environment
    vectors, done = [], 0
    for batch in batches:
        budget = sum(est_tokens(t) for t in batch)
        for attempt in range(MAX_RETRIES):
            try:
                response = client.embeddings.create(model=model, input=batch)
                break
            except RateLimitError:
                wait = 30 * (attempt + 1)
                print(f"  rate-limited; retrying in {wait}s")
                time.sleep(wait)
        else:
            raise RuntimeError(f"rate-limited {MAX_RETRIES} times in a row; giving up")
        vectors.extend(item.embedding for item in response.data)
        done += len(batch)
        print(f"  embedded {done}/{len(texts)}")
        if done < len(texts):
            time.sleep(60 * budget / TPM_LIMIT)  # pace to stay under the TPM cap

    # Voyage (paced the same way; Voyage's base tier allows ~1M+ TPM, so if
    # you switch providers you can likely raise TPM_LIMIT substantially)
    # model = "voyage-3.5-lite"
    # client = voyageai.Client()  # reads VOYAGE_API_KEY from the environment
    # vectors, done = [], 0
    # for batch in batches:
    #     budget = sum(est_tokens(t) for t in batch)
    #     response = client.embed(batch, model=model, input_type="document")
    #     vectors.extend(response.embeddings)
    #     done += len(batch)
    #     print(f"  embedded {done}/{len(texts)}")
    #     if done < len(texts):
    #         time.sleep(60 * budget / TPM_LIMIT)

    # ──────────────────────────────────────────────────────────────────────────

    return np.array(vectors, dtype=np.float32), model


def main() -> None:
    print("fetch:")
    fetch()

    print("chunk:")
    chunks = []
    for book in BOOKS:
        raw = (TEXTS_DIR / book["file"]).read_text(encoding="utf-8")
        content = prune_front_back_matter(strip_gutenberg_boilerplate(raw), book)
        book_chunks = chunk_book(content, book["source"])
        print(f"  {len(book_chunks):4d} chunks  {book['source']}")
        chunks.extend(book_chunks)
    total_tokens = sum(est_tokens(c["text"]) for c in chunks)
    print(f"  {len(chunks):4d} chunks total (~{total_tokens / 1000:.0f}K tokens to embed)")

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
