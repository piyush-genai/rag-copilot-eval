# Decision 001 — Chunking Strategy

**Date:** 2026-04-17  
**Status:** Accepted  
**Component:** `ingestion/chunker.py`

---

## Context

The corpus consists of ~200 technical operations runbooks converted from Markdown to PDF. Before selecting a chunking strategy, the data was explored directly (see `docs/corpus_findings.md`). The key structural properties observed:

- Documents have detectable section boundaries (Overview, Prerequisites, Steps, Troubleshooting, etc.)
- Steps are narrative prose followed by bash command blocks — no explicit step numbers
- Sections answer different classes of questions and should never be mixed in a single chunk
- Cross-step references are local (adjacent steps), not non-local

---

## Decision

**Section-aware sliding window chunking.**

Section boundaries are detected first. The sliding window is applied within each section independently. No chunk ever spans two sections.

Parameters:
- `CHUNK_SIZE_TOKENS = 400`
- `OVERLAP_TOKENS = 30`
- `MIN_CHUNK_TOKENS = 100`
- Encoding: `cl100k_base` (matches Titan Embeddings V2 tokenisation)

---

## Alternatives Considered

| Strategy | Reason Rejected |
|---|---|
| Fixed-size sliding window (no section awareness) | Produces chunks that mix Prerequisites with Steps — diluted embedding vectors, poor retrieval precision |
| Semantic sentence grouping | Requires an embedding call per sentence at ingestion time — expensive for 200 documents. Section boundaries are detectable with regex, making this overkill. |
| Document-level (no chunking) | Runbooks are multi-page. A document-level vector represents the full mix of content — precision collapses for specific queries. |
| Hierarchical (parent-child) | Valid future improvement. Adds implementation complexity not justified at this stage. Noted as a planned enhancement. |

---

## Consequences

- Retrieval precision is high for section-specific queries ("how do I troubleshoot X") because chunks are semantically pure within their section
- Documents that fail section detection fall back to "Full Document" — these still get indexed but lose section-level filtering capability
- The 30-token overlap handles local cross-step references. Non-local references ("run the command from step 2") are addressed via citations in the response, not by expanding overlap
- Trailing micro-chunks below 100 tokens are merged backward into the previous chunk rather than discarded — preserves verification steps and rollback notes that are short but operationally critical
