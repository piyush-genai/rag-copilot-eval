# PURPOSE: Unit tests for retrieval/faiss_fallback.py — validates FAISS index operations
#          without making any Bedrock API calls (uses synthetic embeddings)
# CALLED BY: pytest (python -m pytest tests/test_faiss_fallback.py -v)
# DEPENDS ON: retrieval.faiss_fallback, numpy, pytest

import os
import sys
import tempfile

# Why this sys.path line: Python needs to find the retrieval/ package.
# When pytest runs from the project root, it might not see the package.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
import pytest

from retrieval.faiss_fallback import FAISSVectorStore, SearchResult, EMBEDDING_DIM


# ─── SHARED TEST HELPERS ──────────────────────────────────────────────────────

def make_random_embedding() -> list[float]:
    """
    Generate a random unit-normalised 1536-dim vector.

    Why unit-normalised: FAISSVectorStore normalises vectors before indexing.
    Using pre-normalised vectors in tests makes score assertions predictable.
    """
    vec = np.random.randn(EMBEDDING_DIM).astype(np.float32)
    vec = vec / np.linalg.norm(vec)  # L2-normalise: magnitude becomes 1.0
    return vec.tolist()


def make_chunk(
    chunk_id: str = "abc123",
    text: str = "restart the payment service",
    source_runbook: str = "runbooks/payment.pdf",
    section_name: str = "Steps",
    service_name: str = "payment-api",
    embedding: list[float] = None,
) -> dict:
    """
    Build a minimal chunk dict that FAISSVectorStore.add_chunks() accepts.
    Mirrors the structure produced by chunker.py + embedder.py.
    """
    return {
        "chunk_id": chunk_id,
        "text": text,
        "source_runbook": source_runbook,
        "section_name": section_name,
        "page_num": 1,
        "service_name": service_name,
        "team_owner": "",
        "severity_level": "unknown",
        "embedding": embedding or make_random_embedding(),
    }


# ─── TEST 1: Empty index returns empty results ────────────────────────────────

def test_empty_index_returns_empty_results():
    """
    Searching an empty FAISS index should return an empty list, not crash.

    Why this matters: lambda_handler.py might call search() before any chunks
    have been indexed (e.g. first run, or after a failed ingestion). The system
    must degrade gracefully, not raise an exception.
    """
    store = FAISSVectorStore()
    query = make_random_embedding()

    results = store.search(query, k=5)

    assert results == [], (
        f"Expected empty list from empty index, got {results}"
    )


# ─── TEST 2: Added chunks are retrievable ─────────────────────────────────────

def test_added_chunks_are_retrievable():
    """
    After adding chunks, search should return results.

    Why this matters: verifies the basic add → search pipeline works.
    If add_chunks() silently fails, search() would return nothing and
    the entire retrieval system would be broken.
    """
    store = FAISSVectorStore()

    # Add 5 chunks with random embeddings.
    chunks = [make_chunk(chunk_id=f"chunk_{i}", text=f"step {i}") for i in range(5)]
    store.add_chunks(chunks)

    assert store.total_vectors == 5, (
        f"Expected 5 vectors in index, got {store.total_vectors}"
    )

    # Search should return results now.
    query = make_random_embedding()
    results = store.search(query, k=3)

    assert len(results) == 3, (
        f"Expected 3 results, got {len(results)}"
    )

    # Every result must be a SearchResult with the required fields.
    for r in results:
        assert isinstance(r, SearchResult)
        assert r.chunk_id.startswith("chunk_")
        assert r.score >= -0.1  # cosine similarity of random vectors is near 0, can be slightly negative


# ─── TEST 3: Most similar vector ranks first ──────────────────────────────────

def test_most_similar_vector_ranks_first():
    """
    The chunk whose embedding is most similar to the query should be rank 1.

    Why this matters: this is the core correctness guarantee of the vector store.
    If the ranking is wrong, engineers get irrelevant runbook sections during
    incidents — the entire system fails its purpose.

    Strategy: create one chunk whose embedding IS the query vector (cosine
    similarity = 1.0). It must always be the top result.
    """
    store = FAISSVectorStore()

    # Create a specific query vector.
    query = make_random_embedding()

    # Create one chunk whose embedding matches the query exactly.
    # Why exact match: cosine similarity of identical vectors = 1.0.
    # This chunk must always be rank 1 regardless of other chunks.
    exact_match_chunk = make_chunk(
        chunk_id="exact_match",
        text="this chunk matches the query exactly",
        embedding=query  # same vector as the query
    )

    # Add the exact match plus 9 random chunks.
    random_chunks = [make_chunk(chunk_id=f"random_{i}") for i in range(9)]
    store.add_chunks([exact_match_chunk] + random_chunks)

    results = store.search(query, k=5)

    assert len(results) > 0, "Expected at least 1 result"
    assert results[0].chunk_id == "exact_match", (
        f"Expected 'exact_match' as top result, got '{results[0].chunk_id}'. "
        f"Top score: {results[0].score:.4f}"
    )
    # Score should be very close to 1.0 (exact cosine match).
    assert results[0].score > 0.99, (
        f"Expected score ~1.0 for exact match, got {results[0].score:.4f}"
    )


# ─── TEST 4: Service filter works correctly ───────────────────────────────────

def test_service_filter_excludes_other_services():
    """
    When service_filter is set, only chunks from that service should be returned.

    Why this matters: during a P1 incident for the payments service, the engineer
    should not see runbook chunks from the database or nginx service. The filter
    is what makes service-scoped queries possible.

    Why post-filter (not pre-filter): FAISS has no native metadata filtering.
    We retrieve k*2 candidates and filter afterward. This test verifies the
    post-filter logic works correctly.
    """
    store = FAISSVectorStore()

    # Add chunks from two different services.
    payment_chunks = [
        make_chunk(chunk_id=f"pay_{i}", service_name="payment-api")
        for i in range(5)
    ]
    database_chunks = [
        make_chunk(chunk_id=f"db_{i}", service_name="database")
        for i in range(5)
    ]
    store.add_chunks(payment_chunks + database_chunks)

    # Search with service_filter="payment-api".
    query = make_random_embedding()
    results = store.search(query, k=10, service_filter="payment-api")

    # Every result must be from payment-api.
    for r in results:
        assert r.service_name == "payment-api", (
            f"Expected service_name='payment-api', got '{r.service_name}' "
            f"for chunk_id='{r.chunk_id}'"
        )


# ─── TEST 5: Save and load round-trip ─────────────────────────────────────────

def test_save_and_load_round_trip():
    """
    Saving and loading the FAISS index must produce identical search results.

    Why this matters: the ingestion pipeline runs once (or on new uploads).
    The retrieval service loads the saved index on startup. If save/load
    corrupts the index, every query after a service restart returns wrong results.

    Why tempfile: avoids leaving test artifacts on disk. The temp directory
    is cleaned up automatically after the test.
    """
    store = FAISSVectorStore()

    # Add chunks with a known exact-match chunk.
    query = make_random_embedding()
    exact_match = make_chunk(chunk_id="saved_exact", embedding=query)
    store.add_chunks([exact_match] + [make_chunk(chunk_id=f"r_{i}") for i in range(4)])

    # Save to a temporary directory.
    with tempfile.TemporaryDirectory() as tmpdir:
        index_path = os.path.join(tmpdir, "test.bin")
        metadata_path = os.path.join(tmpdir, "test.pkl")

        store.save(index_path, metadata_path)

        # Load into a fresh store.
        loaded_store = FAISSVectorStore()
        loaded_store.load(index_path, metadata_path)

        # Search the loaded store.
        results = loaded_store.search(query, k=3)

        assert len(results) > 0, "Loaded store returned no results"
        assert results[0].chunk_id == "saved_exact", (
            f"Expected 'saved_exact' as top result after load, "
            f"got '{results[0].chunk_id}'"
        )
        assert results[0].score > 0.99, (
            f"Expected score ~1.0 after load, got {results[0].score:.4f}"
        )


# ─── TEST 6: Missing embedding raises RuntimeError ────────────────────────────

def test_missing_embedding_raises_error():
    """
    Adding a chunk without an embedding should raise RuntimeError immediately.

    Why this matters: a chunk without an embedding means embedder.py failed
    silently. If we let it through, FAISS would receive a None value and
    crash with a cryptic C++ error. Catching it here gives a clear message.
    """
    store = FAISSVectorStore()

    # Create a chunk with no embedding field.
    bad_chunk = {
        "chunk_id": "no_embedding",
        "text": "this chunk has no embedding",
        "source_runbook": "test.pdf",
        "section_name": "Steps",
        "page_num": 1,
        "service_name": "",
        "team_owner": "",
        "severity_level": "unknown",
        # "embedding" key is intentionally missing
    }

    with pytest.raises(RuntimeError, match="no embedding"):
        store.add_chunks([bad_chunk])
