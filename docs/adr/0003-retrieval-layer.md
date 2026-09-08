# ADR-0003: Retrieval over public-domain texts, numpy instead of a vector database

- **Status:** Accepted
- **Decided:** 2026-06-11 (`03c8f18`)
- **Recorded:** 2026-09-08 — written retroactively from CLAUDE.md
- **Applies to:** `scripts/build_index.py`, `api/index.py`, `api/_index/`, `data/texts/`

## Context

The persona is a psychoanalyst, and a persona that improvises its theory is
thin. Grounding replies in real source text makes the character substantially
better — but the corpus is small (~3,800 chunks), the backend is a Vercel
serverless function with cold starts to care about, and the texts themselves
carry a copyright constraint that is easy to get wrong.

## Decision

Ground every reply in retrieved passages from nine public-domain works of Freud
and Jung, using a hand-rolled numpy retrieval layer.

**Corpus.** Pre-1929 translations only — Eder, Brill, Hall, Hinkle, Kuttner,
Long. **Never the Strachey *Standard Edition*, which is still in copyright.**
Reich and Fromm have no public-domain English translations and are therefore out.

**Same embedding model on both sides.** The corpus (`build_index.py`) and the
runtime query (`api/index.py`) must embed with the same model. Both files carry
paired `EMBEDDING PROVIDER` comment-toggles (OpenAI default, Voyage
alternative), and the runtime asserts dimension equality so a mismatch fails
loudly rather than returning nonsense.

**Offline/online split.** Embeddings are precomputed and committed —
`api/_index/embeddings.npy` (float16, row-normalised) plus `chunks.json`. At
runtime the function embeds *only the query*. Never load model weights into the
function; never add a vector database at this corpus size. Cosine similarity is
a plain dot product over a flat matrix, `argpartition` for the top 4, filtered by
`MIN_SIMILARITY`. pgvector is the known upgrade path if the corpus ever grows
enough to need one.

**Graceful degradation.** A missing index or a failed embedding call yields
ungrounded chat — never a 500. A retrieval hiccup must not take down the
conversation.

**Persona survives grounding.** Retrieved passages are appended to the system
prompt under `GROUNDING_PREAMBLE`, which re-asserts the 1–3 sentence limit and
forbids the Analyst from mentioning that he consulted anything.

**Corpus pruning lives in the script.** Per-book `start`/`end` regex markers in
`BOOKS` cut title pages, TOCs, translator boilerplate and indices before
chunking, while keeping substantive prose (author prefaces, Hinkle's analytical
introduction). **Never hand-edit the committed source texts** — they must stay
byte-identical to a fresh Gutenberg fetch, or the pruning markers rot silently.

**Embedding rate limits.** Requests are token-budgeted (≤25K estimated tokens
each) and paced against `TPM_LIMIT` (40K, the OpenAI free tier) with
retry-on-429. Raise `TPM_LIMIT` on a paid tier.

## Consequences

- The index is a build artefact that lives in git. Rebuilding needs a key;
  `--chunks-only` runs fetch + chunk with no key and is the cheap way to confirm
  the committed index is still reproducible (it should report 3,807 chunks).
- Changing the embedding model is a two-file change plus a full rebuild. There is
  no way to change one side safely.
- Retrieval quality is bounded by what these particular translations contain.
  That is an accepted cost of the copyright constraint.
