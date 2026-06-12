"""Chunker invariants, run against the real committed corpus texts.

These pin down the boundaries we calibrated by hand: if a re-fetched text or
a marker edit shifts where a book starts or ends, these fail loudly instead
of silently embedding a table of contents.
"""

import pytest

from build_index import (
    BOOKS,
    BATCH_TOKEN_BUDGET,
    MAX_TOKENS,
    TEXTS_DIR,
    chunk_book,
    est_tokens,
    prune_front_back_matter,
    split_oversized,
    strip_gutenberg_boilerplate,
    token_budgeted_batches,
)

# First words of the first chunk / last words of the last chunk per book,
# matching the hand-calibrated prune boundaries.
EXPECTED_BOUNDS = {
    "freud_dream_psychology.txt": (
        'In what we may term "prescientific days"',
        "by the indestructible wish.",
    ),
    "freud_three_contributions.txt": (
        "Although the author is fully aware of the gaps",
        "somatic sexual manifestation of former years.",
    ),
    "freud_general_introduction.txt": (
        "I do not know how familiar some of you may be",
        "There are fagots and fagots.",
    ),
    "jung_psychology_of_the_unconscious.txt": (
        "When Professor Freud of Vienna made his early discoveries",
        "“The Myth of the Birth of the Hero.”)",
    ),
    "freud_psychopathology.txt": (
        "During the year 1898 I published a short essay",
        "not robbed of all capacity to express itself_.",
    ),
    "freud_wit.txt": (
        "Whoever has had occasion to examine that part of the literature",
        "did not need humor to make us happy.",
    ),
    "freud_leonardo.txt": (
        "When psychoanalytic investigation, which usually contents itself",
        "M. Herzfeld, l. c. p. II.",
    ),
    "freud_war_and_death.txt": (
        "Caught in the whirlwind of these war times",
        "[5] See Totem and Taboo, Chapter III.",
    ),
    "jung_collected_papers.txt": (
        "In that wide field of psychopathic deficiency",
        "tendency of the psychological process at any given moment.",
    ),
}


def book_chunks(book):
    raw = (TEXTS_DIR / book["file"]).read_text(encoding="utf-8")
    content = prune_front_back_matter(strip_gutenberg_boilerplate(raw), book)
    return chunk_book(content, book["source"])


@pytest.mark.parametrize("book", BOOKS, ids=lambda b: b["file"])
def test_prune_markers_found_and_chunks_nonempty(book):
    chunks = book_chunks(book)
    assert len(chunks) > 50  # a real book, not an accidentally-empty slice


@pytest.mark.parametrize("book", BOOKS, ids=lambda b: b["file"])
def test_chunk_sizes_within_cap(book):
    # +5 tolerance: est_tokens() integer rounding can land a hair over.
    sizes = [est_tokens(c["text"]) for c in book_chunks(book)]
    assert max(sizes) <= MAX_TOKENS + 5


@pytest.mark.parametrize("book", BOOKS, ids=lambda b: b["file"])
def test_prune_boundaries_match_calibration(book):
    first_expected, last_expected = EXPECTED_BOUNDS[book["file"]]
    chunks = book_chunks(book)
    assert chunks[0]["text"].startswith(first_expected)
    assert chunks[-1]["text"].endswith(last_expected)


def test_every_chunk_carries_source():
    for book in BOOKS:
        assert all(c["source"] == book["source"] for c in book_chunks(book))


def test_split_oversized_caps_paragraphs():
    monster = "This is a sentence. " * 400  # ~2,600 est. tokens
    pieces = split_oversized(monster.strip())
    assert len(pieces) > 1
    assert all(est_tokens(p) <= MAX_TOKENS for p in pieces)


def test_token_budgeted_batches_respect_budget_and_order():
    texts = [f"word {'filler ' * (i % 700)}{i}" for i in range(60)]
    batches = token_budgeted_batches(texts)
    for batch in batches:
        assert sum(est_tokens(t) for t in batch) <= BATCH_TOKEN_BUDGET
    flattened = [t for batch in batches for t in batch]
    assert flattened == texts  # nothing dropped, nothing reordered
