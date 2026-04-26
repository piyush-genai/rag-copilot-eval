# PURPOSE: Unit tests for ingestion/chunker.py
# CALLED BY: pytest (run with: python -m pytest tests/test_chunker.py -v)
# DEPENDS ON: ingestion/chunker.py, tiktoken, pytest

# What are unit tests?
# A unit test calls one function with known input and checks the output is
# exactly what you expect. If the function breaks later (e.g. you change a
# parameter), the test fails and tells you immediately.
# "Unit" = one function, tested in isolation.

import sys
import os

# Why this sys.path line: Python needs to know where to find ingestion/chunker.py.
# When pytest runs from the project root, it might not see the ingestion/ folder.
# This line adds the project root to Python's search path.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import tiktoken
from ingestion.chunker import chunk_section, CHUNK_SIZE_TOKENS, MIN_CHUNK_TOKENS, ENCODING


# ─── SHARED TEST HELPERS ──────────────────────────────────────────────────────

def count_tokens(text: str) -> int:
    """Count how many tokens a string contains. Used in assertions below."""
    enc = tiktoken.get_encoding(ENCODING)
    return len(enc.encode(text))


def make_metadata(runbook="test.pdf", section="Steps") -> dict:
    """Return a minimal metadata dict. Avoids repeating this in every test."""
    return {
        "source_runbook": runbook,
        "section_name": section,
        "service_name": "test-service",
        "team_owner": "test-team",
        "severity_level": "P2",
        "page_num": 1,
    }


# ─── TEST 1: Short section returns exactly one chunk ─────────────────────────

def test_short_section_returns_single_chunk():
    """
    If a section is shorter than CHUNK_SIZE_TOKENS, it should come back
    as exactly one chunk — no splitting needed.

    Why this matters: short sections like "Prerequisites: None" or
    "Overview: See main runbook." are valid answers. They must not be
    discarded or duplicated.
    """
    # This text is short — well under 400 tokens.
    short_text = "SSH into the server and run: systemctl restart payment-api. Verify with: systemctl status payment-api."

    chunks = chunk_section(short_text, make_metadata())

    # Assert: we got exactly 1 chunk
    assert len(chunks) == 1, (
        f"Expected 1 chunk for short section, got {len(chunks)}"
    )

    # Assert: the chunk text matches what we put in (no content lost)
    assert short_text in chunks[0]["text"], (
        "Chunk text does not contain the original section text"
    )

    # Assert: chunk_index is 0 (first and only chunk)
    assert chunks[0]["chunk_index"] == 0


# ─── TEST 2: Long section produces multiple chunks with overlap ───────────────

def test_long_section_produces_overlap():
    """
    A section longer than CHUNK_SIZE_TOKENS should produce multiple chunks.
    Adjacent chunks should share content (the overlap).

    Why this matters: overlap is the core mechanism for preserving cross-step
    references. If overlap is broken, "run the command from step 2" loses
    its context.
    """
    # Create text long enough to produce 2+ chunks that each exceed MIN_CHUNK_TOKENS.
    # With CHUNK_SIZE=400, OVERLAP=30, MIN_CHUNK=100:
    # chunk 1 = tokens 0-400, chunk 2 starts at 370.
    # To ensure chunk 2 has >= 100 tokens: need total > 400 + 100 = 500 tokens.
    # Use 900 tokens to guarantee at least 2 full-sized chunks with no micro-chunk.
    # "runbook step " ≈ 3 tokens per repeat → 300 repeats ≈ 900 tokens.
    long_text = "runbook step " * 300  # ~900 tokens

    chunks = chunk_section(long_text, make_metadata())

    # Assert: more than one chunk was produced
    assert len(chunks) > 1, (
        f"Expected multiple chunks for long section, got {len(chunks)}"
    )

    # Assert: adjacent chunks share content (overlap exists).
    # Strategy: take the last 10 words of chunk[0] and check they appear
    # somewhere in chunk[1]. Not checking exact token overlap because
    # _find_safe_split_point may adjust boundaries slightly.
    chunk0_words = chunks[0]["text"].split()
    chunk1_text = chunks[1]["text"]

    # Take last 5 words of chunk 0
    last_words_of_chunk0 = " ".join(chunk0_words[-5:])

    assert last_words_of_chunk0 in chunk1_text, (
        f"Expected overlap: last words of chunk 0 should appear in chunk 1.\n"
        f"Last words of chunk 0: '{last_words_of_chunk0}'\n"
        f"Start of chunk 1: '{chunk1_text[:100]}'"
    )


# ─── TEST 3: Trailing micro-chunk merges into previous chunk ──────────────────

def test_trailing_micro_chunk_merges():
    """
    If the last chunk would be smaller than MIN_CHUNK_TOKENS, it should be
    merged into the previous chunk — not returned as a standalone tiny chunk.

    Why this matters: a 30-token trailing chunk like "See Section 4." is
    not a retrievable answer. Indexing it wastes embedding API calls and
    adds noise to the vector store.
    """
    # We need text where the last window produces a micro-chunk.
    # Strategy: make text that is exactly CHUNK_SIZE + a tiny bit.
    # 410 tokens of normal words + 10 tokens of a trailing note.
    enc = tiktoken.get_encoding(ENCODING)

    # Build main body: 410 tokens
    main_body = "operational step detail " * 103  # ~412 tokens

    # Build tiny tail: well under MIN_CHUNK_TOKENS (100 tokens)
    tiny_tail = " See escalation guide for more."  # ~8 tokens

    full_text = main_body + tiny_tail

    chunks = chunk_section(full_text, make_metadata())

    # Assert: every chunk meets the minimum token threshold EXCEPT we verify
    # the tiny tail was absorbed (not a standalone chunk under 100 tokens).
    for i, chunk in enumerate(chunks):
        token_count = count_tokens(chunk["text"])
        assert token_count >= MIN_CHUNK_TOKENS, (
            f"Chunk {i} has {token_count} tokens — below MIN_CHUNK_TOKENS ({MIN_CHUNK_TOKENS}). "
            f"Trailing micro-chunk was not merged correctly.\n"
            f"Chunk text: '{chunk['text'][:80]}...'"
        )

    # Assert: tiny tail content is present somewhere (not discarded entirely)
    all_text = " ".join(c["text"] for c in chunks)
    assert "escalation guide" in all_text, (
        "Tiny tail was discarded instead of merged. Content lost."
    )


# ─── TEST 4: chunk_id is deterministic ───────────────────────────────────────

def test_chunk_id_is_deterministic():
    """
    Running chunk_section twice on the same input must produce the same
    chunk IDs.

    Why this matters: index_writer.py uses chunk_id to upsert documents in
    OpenSearch. If IDs were random (UUID), every re-ingest would create
    duplicates instead of updating existing chunks. The deterministic ID
    is what makes idempotent re-ingestion possible.
    """
    text = "deploy the service using the following procedure " * 50  # ~250 tokens
    meta = make_metadata(runbook="payments/restart.pdf", section="Procedure")

    # Run chunk_section twice with identical input
    chunks_run1 = chunk_section(text, meta)
    chunks_run2 = chunk_section(text, meta)

    # Assert: same number of chunks both times
    assert len(chunks_run1) == len(chunks_run2), (
        "Different number of chunks on second run — chunking is non-deterministic"
    )

    # Assert: every chunk has the same ID in both runs
    for i, (c1, c2) in enumerate(zip(chunks_run1, chunks_run2)):
        assert c1["chunk_id"] == c2["chunk_id"], (
            f"Chunk {i} has different IDs on two runs.\n"
            f"Run 1: {c1['chunk_id']}\n"
            f"Run 2: {c2['chunk_id']}"
        )

    # Assert: different source_runbook produces different chunk_id
    # (no cross-document ID collisions)
    meta_different = make_metadata(runbook="database/failover.pdf", section="Procedure")
    chunks_different = chunk_section(text, meta_different)

    assert chunks_run1[0]["chunk_id"] != chunks_different[0]["chunk_id"], (
        "Two chunks from different runbooks produced the same ID — collision risk."
    )


# ─── TEST 5: Metadata is preserved in every chunk ────────────────────────────

def test_metadata_preserved_in_all_chunks():
    """
    Every chunk must carry the full metadata dict from its parent section.

    Why this matters: retrieval filters by service_name and severity_level.
    If a chunk is missing its metadata, it becomes unretrievable for filtered
    queries — the engineer can't find it during an incident.
    """
    long_text = "service operation procedure " * 200  # ~600 tokens → 2+ chunks

    meta = {
        "source_runbook": "runbooks/ssl-rotation.pdf",
        "section_name": "Rollback",
        "service_name": "payments-api",
        "team_owner": "platform-reliability",
        "severity_level": "P1",
        "page_num": 3,
    }

    chunks = chunk_section(long_text, meta)

    assert len(chunks) > 1, "Need multiple chunks to test metadata propagation"

    for i, chunk in enumerate(chunks):
        # Every metadata key must be present in every chunk
        for key, expected_value in meta.items():
            assert key in chunk, (
                f"Chunk {i} is missing metadata key '{key}'"
            )
            assert chunk[key] == expected_value, (
                f"Chunk {i} has wrong value for '{key}'.\n"
                f"Expected: {expected_value}\n"
                f"Got: {chunk[key]}"
            )# PURPOSE: Unit tests for the semantic chunker — validates chunk size bounds and overlap correctness
# CALLED BY: pytest
# DEPENDS ON: ingestion.chunker, pytest
