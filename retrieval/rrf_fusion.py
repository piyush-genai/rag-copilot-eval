# PURPOSE: Merges BM25 and KNN result lists using Reciprocal Rank Fusion (k=60) into a unified ranking
# CALLED BY: retrieval.retriever
# DEPENDS ON: Nothing (pure Python)

from __future__ import annotations

import logging

from retrieval.faiss_fallback import SearchResult

logger = logging.getLogger(__name__)


# ─── CONFIGURATION ────────────────────────────────────────────────────────────

RRF_K = 60
# Why 60: empirically established standard default.
# Low k (e.g. 5): rank 1 gets 1/6=0.167, rank 2 gets 1/7=0.143 — huge gap,
#   over-weights the top result from each list.
# High k (e.g. 200): every rank gets ~0.005 — everything is nearly equal,
#   fusion adds no signal.
# k=60 gives enough differentiation without over-weighting rank 1.
# Formula: score(doc) = Σ 1 / (k + rank_i(doc))
# where rank_i is the document's 1-indexed position in list i.


# ─── PUBLIC FUNCTION ──────────────────────────────────────────────────────────

def reciprocal_rank_fusion(
    bm25_results: list[SearchResult],
    dense_results: list[SearchResult],
    top_k: int = 40,
) -> list[SearchResult]:
    """
    Fuse two ranked result lists using Reciprocal Rank Fusion.

    Why RRF over score averaging:
    BM25 scores range from 0 to 15+. Cosine similarity ranges from 0 to 1.
    Averaging them directly lets BM25 dominate regardless of semantic relevance
    — the scales are incompatible. RRF uses only rank positions, not raw scores,
    so it is completely scale-agnostic.

    A document ranked #1 in BM25 and #8 in dense:
      score = 1/(60+1) + 1/(60+8) = 0.0164 + 0.0147 = 0.0311

    A document ranked #4 in both lists:
      score = 1/(60+4) + 1/(60+4) = 0.0156 + 0.0156 = 0.0313

    Both scores are nearly identical — both documents are consistently relevant.
    RRF rewards consistency across methods, not dominance in one method.

    Args:
        bm25_results: Ranked list from BM25 search (rank 1 = index 0).
        dense_results: Ranked list from KNN/dense search (rank 1 = index 0).
        top_k: Number of results to return after fusion.

    Returns:
        Fused list of SearchResult, sorted by RRF score descending.
        The score field on each result is replaced with the RRF score.
    """
    # rrf_scores maps chunk_id → accumulated RRF score across all lists.
    # Why a dict keyed by chunk_id: the same document may appear in both
    # BM25 and dense results. We accumulate its score from both lists.
    rrf_scores: dict[str, float] = {}

    # chunk_map maps chunk_id → SearchResult object.
    # Why store the object: we need to return SearchResult objects, not just
    # scores. The last-seen object for a chunk_id is used (both lists have
    # the same content for the same chunk_id).
    chunk_map: dict[str, SearchResult] = {}

    # ── Score from BM25 rankings ──────────────────────────────────────────────
    # enumerate starts at 0, but RRF ranks are 1-indexed.
    # Why 1-indexed: rank 0 would give 1/(60+0) = 1/60 = 0.0167, which is
    # the same as rank 1 in a 0-indexed scheme. Using 1-indexed ranks is the
    # standard RRF formulation.
    for rank, result in enumerate(bm25_results, start=1):
        rrf_scores[result.chunk_id] = (
            rrf_scores.get(result.chunk_id, 0.0) + 1.0 / (RRF_K + rank)
        )
        chunk_map[result.chunk_id] = result

    # ── Score from dense rankings ─────────────────────────────────────────────
    for rank, result in enumerate(dense_results, start=1):
        rrf_scores[result.chunk_id] = (
            rrf_scores.get(result.chunk_id, 0.0) + 1.0 / (RRF_K + rank)
        )
        # Why overwrite chunk_map: if the same chunk appears in both lists,
        # the SearchResult content is identical. Either copy is fine.
        chunk_map[result.chunk_id] = result

    # ── Sort by RRF score and return top_k ────────────────────────────────────
    # Sort chunk_ids by their accumulated RRF score, highest first.
    # Why sorted(..., reverse=True): higher RRF score = more consistently
    # relevant across both retrieval methods = should rank higher.
    sorted_chunk_ids = sorted(
        rrf_scores.keys(),
        key=lambda cid: rrf_scores[cid],
        reverse=True
    )

    # Build the output list, replacing each result's score with its RRF score.
    # Why replace score: the original score (BM25 or cosine) is on a different
    # scale. Replacing with RRF score makes the output list self-consistent —
    # the score field always means "RRF relevance" after fusion.
    fused_results = []
    for chunk_id in sorted_chunk_ids[:top_k]:
        result = chunk_map[chunk_id]

        # Create a new SearchResult with the RRF score.
        # Why not mutate in place: SearchResult is a dataclass. Mutating the
        # original would affect the caller's bm25_results or dense_results lists.
        fused_results.append(SearchResult(
            score=rrf_scores[chunk_id],   # RRF score replaces original score
            chunk_id=result.chunk_id,
            chunk_text=result.chunk_text,
            source_runbook=result.source_runbook,
            section_name=result.section_name,
            page_num=result.page_num,
            service_name=result.service_name,
            team_owner=result.team_owner,
            severity_level=result.severity_level,
        ))

    logger.debug(
        "RRF fusion: %d BM25 + %d dense → %d unique → top %d returned",
        len(bm25_results), len(dense_results), len(rrf_scores), len(fused_results)
    )

    return fused_results
