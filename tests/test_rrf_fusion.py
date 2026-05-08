# PURPOSE: Unit tests for retrieval/rrf_fusion.py — validates RRF score calculation and ranking
# CALLED BY: pytest (python -m pytest tests/test_rrf_fusion.py -v)
# DEPENDS ON: retrieval.rrf_fusion, retrieval.faiss_fallback (SearchResult), pytest

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from retrieval.faiss_fallback import SearchResult
from retrieval.rrf_fusion import reciprocal_rank_fusion, RRF_K


# ─── SHARED TEST HELPERS ──────────────────────────────────────────────────────

def make_result(chunk_id: str, score: float = 1.0, service: str = "svc") -> SearchResult:
    """Build a minimal SearchResult for testing."""
    return SearchResult(
        score=score,
        chunk_id=chunk_id,
        chunk_text=f"text for {chunk_id}",
        source_runbook="test.pdf",
        section_name="Steps",
        page_num=1,
        service_name=service,
        team_owner="",
        severity_level="unknown",
    )


# ─── TEST 1: Empty inputs return empty output ─────────────────────────────────

def test_empty_inputs_return_empty():
    """
    Both empty lists should return an empty fused list.

    Why this matters: retriever.py may call RRF with empty lists if both
    search methods return no results. RRF must not crash.
    """
    result = reciprocal_rank_fusion([], [])
    assert result == []


def test_one_empty_list_uses_other():
    """
    If one list is empty, RRF should still return results from the other.

    Why this matters: if BM25 returns no results (e.g. query has no matching
    tokens), RRF should still return the dense results ranked by their position.
    """
    dense = [make_result("d1"), make_result("d2"), make_result("d3")]
    result = reciprocal_rank_fusion([], dense)

    assert len(result) == 3
    # d1 was rank 1 in dense, should be rank 1 in fused output.
    assert result[0].chunk_id == "d1"


# ─── TEST 2: RRF score formula is correct ────────────────────────────────────

def test_rrf_score_formula():
    """
    Verify the RRF score is calculated as 1/(k + rank) summed across lists.

    Why this matters: the formula is the core of RRF. If it's wrong, the
    entire fusion ranking is wrong. This test pins the exact expected values.
    """
    # One document ranked #1 in BM25 only.
    # Expected score: 1/(60+1) = 0.01639...
    bm25 = [make_result("only_bm25")]
    dense = [make_result("only_dense")]

    result = reciprocal_rank_fusion(bm25, dense, top_k=10)

    # Find the scores for each chunk.
    scores = {r.chunk_id: r.score for r in result}

    expected_bm25_score = 1.0 / (RRF_K + 1)
    expected_dense_score = 1.0 / (RRF_K + 1)

    assert abs(scores["only_bm25"] - expected_bm25_score) < 1e-6, (
        f"Expected {expected_bm25_score:.6f}, got {scores['only_bm25']:.6f}"
    )
    assert abs(scores["only_dense"] - expected_dense_score) < 1e-6


# ─── TEST 3: Document in both lists gets higher score ─────────────────────────

def test_document_in_both_lists_scores_higher():
    """
    A document appearing in both BM25 and dense results should score higher
    than a document appearing in only one list.

    Why this matters: this is the core value of RRF. A document that is
    consistently relevant across both retrieval methods should rank higher
    than one that is only relevant to one method.
    """
    # "shared" appears in both lists at rank 1.
    # "bm25_only" appears only in BM25 at rank 2.
    bm25 = [make_result("shared"), make_result("bm25_only")]
    dense = [make_result("shared"), make_result("dense_only")]

    result = reciprocal_rank_fusion(bm25, dense, top_k=10)
    scores = {r.chunk_id: r.score for r in result}

    # "shared" score: 1/(60+1) + 1/(60+1) = 2 * 0.01639 = 0.03279
    # "bm25_only" score: 1/(60+2) = 0.01613
    assert scores["shared"] > scores["bm25_only"], (
        f"shared ({scores['shared']:.5f}) should score higher than "
        f"bm25_only ({scores['bm25_only']:.5f})"
    )
    assert scores["shared"] > scores["dense_only"]


# ─── TEST 4: Output is sorted by RRF score descending ─────────────────────────

def test_output_sorted_by_score_descending():
    """
    The fused result list must be sorted highest score first.

    Why this matters: retriever.py passes the fused list directly to the
    reranker. If the list is not sorted, the reranker receives candidates
    in arbitrary order and the top_k slicing is meaningless.
    """
    # Create lists where "winner" appears at rank 1 in both.
    bm25 = [make_result("winner"), make_result("second"), make_result("third")]
    dense = [make_result("winner"), make_result("fourth"), make_result("fifth")]

    result = reciprocal_rank_fusion(bm25, dense, top_k=10)

    # Verify scores are non-increasing.
    for i in range(len(result) - 1):
        assert result[i].score >= result[i + 1].score, (
            f"Result at position {i} (score={result[i].score:.5f}) should be >= "
            f"position {i+1} (score={result[i+1].score:.5f})"
        )

    # "winner" must be first.
    assert result[0].chunk_id == "winner"


# ─── TEST 5: top_k limits output size ─────────────────────────────────────────

def test_top_k_limits_output():
    """
    The output list should never exceed top_k results.

    Why this matters: the reranker receives this list and scores all candidates.
    If top_k is not respected, the reranker processes more candidates than
    expected, increasing latency.
    """
    bm25 = [make_result(f"b{i}") for i in range(20)]
    dense = [make_result(f"d{i}") for i in range(20)]

    result = reciprocal_rank_fusion(bm25, dense, top_k=10)

    assert len(result) <= 10, (
        f"Expected at most 10 results, got {len(result)}"
    )


# ─── TEST 6: Deduplication by chunk_id ────────────────────────────────────────

def test_deduplication_by_chunk_id():
    """
    The same chunk_id appearing in both lists should produce only one result.

    Why this matters: without deduplication, the same chunk would appear twice
    in the fused list. The reranker would score it twice, and the engineer
    would see duplicate results.
    """
    # "dup" appears in both lists.
    bm25 = [make_result("dup"), make_result("unique_b")]
    dense = [make_result("dup"), make_result("unique_d")]

    result = reciprocal_rank_fusion(bm25, dense, top_k=10)

    chunk_ids = [r.chunk_id for r in result]

    # "dup" should appear exactly once.
    assert chunk_ids.count("dup") == 1, (
        f"Expected 'dup' to appear once, got {chunk_ids.count('dup')} times. "
        f"All chunk_ids: {chunk_ids}"
    )

    # Total unique results: "dup", "unique_b", "unique_d" = 3.
    assert len(result) == 3
