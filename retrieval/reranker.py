# PURPOSE: Re-scores fused top-k chunks against the query using a cross-encoder model, returns top-5
# CALLED BY: retrieval.retriever
# DEPENDS ON: sentence-transformers (CrossEncoder), HUGGINGFACE_TOKEN env var

from __future__ import annotations

import logging
import os
import time
from typing import Optional

from retrieval.faiss_fallback import SearchResult

logger = logging.getLogger(__name__)


# ─── CONFIGURATION ────────────────────────────────────────────────────────────

# Cross-encoder model for reranking.
# Why MiniLM-L-6-v2: small enough to run on CPU in ~200ms for 40 candidates.
# Accurate enough to meaningfully reorder hybrid search results.
# Larger models (L-12, large) are more accurate but 3-5x slower — not worth
# the latency cost for this use case.
DEFAULT_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

# Number of final results to return after reranking.
# Why 5: the generator (Claude 3 Sonnet) receives these 5 chunks as context.
# More than 5 dilutes the prompt with lower-quality context. Fewer than 5
# risks missing a relevant chunk that the hybrid search found but ranked lower.
TOP_K_AFTER_RERANK = 5


# ─── PUBLIC CLASS ─────────────────────────────────────────────────────────────

class CrossEncoderReranker:
    """
    Re-scores a list of candidate chunks against a query using a cross-encoder.

    Why two-stage retrieval (hybrid search → reranker):
    Hybrid search with RRF is a voting mechanism — it combines two ranked lists
    but doesn't deeply understand the specific query-chunk relationship. The
    cross-encoder attends to every token in both the query and the chunk
    simultaneously, modelling their interaction directly. Much more accurate,
    but too slow to run on thousands of candidates.

    Pipeline: hybrid search retrieves top-40 fast → reranker scores top-40
    accurately → returns top-5 to the generator.

    Why load model once at startup (not per-request):
    Loading a sentence-transformers model takes ~2-3 seconds and ~500MB RAM.
    Loading per-request would add 2-3 seconds to every query. Loading once
    at startup amortises the cost across all queries.

    Why CPU (not GPU):
    Scoring 40 candidates with MiniLM-L-6 takes ~200ms on CPU. GPU would be
    ~20ms but requires a GPU instance. For this query volume, CPU is sufficient
    and significantly cheaper.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL) -> None:
        # Why lazy import: sentence-transformers is a heavy dependency (~500MB).
        # Importing at module level would slow down every import of this file,
        # even in contexts where the reranker isn't used (e.g. unit tests).
        # Lazy import means the cost is paid only when CrossEncoderReranker
        # is actually instantiated.
        from sentence_transformers import CrossEncoder

        # Set HuggingFace token if available.
        # Why: some cross-encoder models require authentication to download.
        # MiniLM-L-6-v2 is public, but setting the token doesn't hurt.
        hf_token = os.getenv("HUGGINGFACE_TOKEN")
        if hf_token:
            os.environ["HUGGINGFACE_HUB_TOKEN"] = hf_token

        logger.info("Loading cross-encoder model: %s", model_name)
        start = time.time()

        # Load the cross-encoder model.
        # Why device="cpu": see class docstring. CPU is sufficient for 40 candidates.
        self._model = CrossEncoder(model_name, device="cpu")

        elapsed = time.time() - start
        logger.info("Cross-encoder loaded in %.2fs", elapsed)

        self._model_name = model_name

    def rerank(
        self,
        query: str,
        candidates: list[SearchResult],
        top_k: int = TOP_K_AFTER_RERANK,
    ) -> list[SearchResult]:
        """
        Re-score candidates against the query and return the top_k best.

        The cross-encoder scores each (query, chunk_text) pair jointly —
        it sees both texts at once and can model their interaction. This is
        more accurate than the cosine similarity used in dense retrieval,
        which encodes query and document independently.

        Args:
            query: The user's natural language query string.
            candidates: List of SearchResult from RRF fusion (typically top-40).
            top_k: Number of results to return after reranking.

        Returns:
            Top top_k SearchResult objects, sorted by cross-encoder score
            descending. The score field is replaced with the cross-encoder score.

        Raises:
            RuntimeError: If the model fails to score the candidates.
        """
        if not candidates:
            # Edge case: nothing to rerank. Return empty list.
            # Why handle explicitly: calling model.predict([]) raises an error.
            return []

        # Clamp top_k to the number of candidates available.
        # Why: if hybrid search returned only 3 results, we can't return 5.
        effective_top_k = min(top_k, len(candidates))

        try:
            # Build (query, chunk_text) pairs for the cross-encoder.
            # Why pairs: the cross-encoder takes a list of (text_a, text_b) tuples
            # and scores each pair. text_a is the query, text_b is the chunk.
            pairs = [(query, result.chunk_text) for result in candidates]

            start = time.time()

            # Score all pairs in one batch call.
            # Why batch (not one-by-one): the model processes all pairs in a
            # single forward pass, which is significantly faster than N separate
            # calls due to GPU/CPU parallelism and batching overhead.
            scores = self._model.predict(pairs)

            elapsed_ms = (time.time() - start) * 1000
            logger.debug(
                "Cross-encoder scored %d candidates in %.1fms",
                len(candidates), elapsed_ms
            )

            # Pair each candidate with its score, then sort by score descending.
            # Why zip: pairs scores[i] with candidates[i] — same order as the
            # pairs list we built above.
            scored_candidates = sorted(
                zip(scores, candidates),
                key=lambda x: x[0],   # sort by score (first element of tuple)
                reverse=True          # highest score first
            )

            # Build output list with cross-encoder scores replacing original scores.
            # Why replace score: the original score is an RRF score (0.01-0.03 range).
            # The cross-encoder score is a relevance logit (typically -10 to +10).
            # Replacing makes the output score field consistently mean
            # "cross-encoder relevance" for the caller.
            reranked = []
            for score, result in scored_candidates[:effective_top_k]:
                reranked.append(SearchResult(
                    score=float(score),
                    chunk_id=result.chunk_id,
                    chunk_text=result.chunk_text,
                    source_runbook=result.source_runbook,
                    section_name=result.section_name,
                    page_num=result.page_num,
                    service_name=result.service_name,
                    team_owner=result.team_owner,
                    severity_level=result.severity_level,
                ))

            return reranked

        except Exception as e:
            raise RuntimeError(
                f"CrossEncoderReranker failed on query '{query[:50]}...': {e}"
            ) from e
