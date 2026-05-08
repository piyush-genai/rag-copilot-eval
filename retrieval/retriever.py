# PURPOSE: Orchestrates hybrid retrieval — calls OpenSearch (or FAISS fallback), fuses results, reranks
# CALLED BY: gateway.query_handler
# DEPENDS ON: retrieval.opensearch_client, retrieval.faiss_fallback, retrieval.rrf_fusion, retrieval.reranker

from __future__ import annotations

import logging
import os
import time
from typing import Optional

from retrieval.faiss_fallback import FAISSVectorStore, SearchResult
from retrieval.opensearch_client import OpenSearchClient
from retrieval.rrf_fusion import reciprocal_rank_fusion
from retrieval.reranker import CrossEncoderReranker

logger = logging.getLogger(__name__)


# ─── CONFIGURATION ────────────────────────────────────────────────────────────

# Number of candidates to retrieve from each method before fusion.
# Why k*2 (40 candidates from each, 80 total before dedup):
# RRF fusion deduplicates by chunk_id. After fusion we have at most 80 unique
# candidates. The reranker then selects the top 5. Retrieving more candidates
# gives the reranker more to work with, improving final precision.
CANDIDATES_PER_METHOD = 40

# Backend options.
# Why a string toggle (not a class hierarchy): simple to configure via env var.
# "opensearch" = production path (BM25 + KNN + RRF + reranker)
# "faiss"      = local development path (dense-only + reranker, no BM25)
BACKEND_OPENSEARCH = "opensearch"
BACKEND_FAISS = "faiss"


# ─── PUBLIC CLASS ─────────────────────────────────────────────────────────────

class HybridRetriever:
    """
    Orchestrates the full retrieval pipeline: hybrid search → RRF fusion → reranking.

    Why this class exists (not just calling functions directly):
    The retriever needs to manage state — the FAISS index, the OpenSearch client,
    and the reranker model are all expensive to initialise. Loading them once at
    startup and reusing across queries is critical for p95 latency targets.

    Pipeline:
    1. Embed the query (caller's responsibility — query_handler.py does this)
    2. BM25 search (OpenSearch) + KNN search (OpenSearch or FAISS) in parallel
    3. RRF fusion → top-40 unified candidates
    4. Cross-encoder reranker → top-5 final results
    5. Return top-5 to gateway.query_handler for prompt assembly

    Backend toggle:
    - "opensearch": full hybrid (BM25 + KNN + RRF). Production path.
    - "faiss": dense-only (KNN only, no BM25, no RRF). Local development path.
      FAISS fallback also activates automatically if OpenSearch is unreachable.
    """

    def __init__(
        self,
        backend: str = BACKEND_OPENSEARCH,
        faiss_index_path: Optional[str] = None,
        faiss_metadata_path: Optional[str] = None,
    ) -> None:
        """
        Initialise the retriever with the specified backend.

        Args:
            backend: "opensearch" or "faiss". Defaults to RETRIEVAL_BACKEND env var,
                     then "opensearch".
            faiss_index_path: Path to FAISS index file. Used when backend="faiss"
                              or as fallback when OpenSearch is unreachable.
            faiss_metadata_path: Path to FAISS metadata pickle file.
        """
        # Allow env var override of backend.
        # Why env var: Lambda and local dev use different backends without
        # changing code. Set RETRIEVAL_BACKEND=faiss for local development.
        self._backend = os.getenv("RETRIEVAL_BACKEND", backend)

        # Initialise OpenSearch client (lazy — doesn't connect until first query).
        self._opensearch = OpenSearchClient()

        # Initialise FAISS store (used as fallback or primary in faiss mode).
        self._faiss = FAISSVectorStore()
        self._faiss_loaded = False

        # Store paths for lazy FAISS loading.
        self._faiss_index_path = faiss_index_path or "data/faiss_index.bin"
        self._faiss_metadata_path = faiss_metadata_path or "data/faiss_metadata.pkl"

        # Initialise reranker (loads model — takes ~2-3 seconds on first call).
        # Why initialise here (not lazily): the reranker model load is the most
        # expensive operation. Loading it at startup means the first query doesn't
        # pay the 2-3 second penalty.
        self._reranker = CrossEncoderReranker()

        logger.info("HybridRetriever initialised with backend='%s'", self._backend)

    def retrieve(
        self,
        query: str,
        query_embedding: list[float],
        k: int = 5,
        service_filter: Optional[str] = None,
    ) -> list[SearchResult]:
        """
        Run the full retrieval pipeline for a query.

        Args:
            query: The user's natural language query string (for reranker).
            query_embedding: 1536-dim float list from embedder.py (for KNN search).
            k: Number of final results to return (after reranking).
            service_filter: If set, only return chunks from this service_name.

        Returns:
            Top-k SearchResult objects, sorted by cross-encoder score descending.

        Raises:
            RuntimeError: If retrieval fails on both OpenSearch and FAISS.
        """
        start_total = time.time()

        # ── Step 1: Retrieve candidates ───────────────────────────────────────
        bm25_results, dense_results, backend_used = self._retrieve_candidates(
            query, query_embedding, service_filter
        )

        # ── Step 2: Fuse results ──────────────────────────────────────────────
        if backend_used == BACKEND_OPENSEARCH:
            # Full hybrid: fuse BM25 + dense with RRF.
            start_fusion = time.time()
            fused = reciprocal_rank_fusion(
                bm25_results, dense_results, top_k=CANDIDATES_PER_METHOD
            )
            fusion_ms = (time.time() - start_fusion) * 1000
            logger.debug("RRF fusion: %.1fms, %d candidates", fusion_ms, len(fused))
        else:
            # FAISS fallback: dense-only, no BM25 to fuse.
            # Why skip RRF: RRF requires two lists. With only dense results,
            # there's nothing to fuse — just use the dense results directly.
            fused = dense_results
            logger.debug("FAISS mode: skipping RRF, using %d dense candidates", len(fused))

        if not fused:
            logger.warning("No candidates after fusion for query: '%s'", query[:50])
            return []

        # ── Step 3: Rerank ────────────────────────────────────────────────────
        start_rerank = time.time()
        reranked = self._reranker.rerank(query, fused, top_k=k)
        rerank_ms = (time.time() - start_rerank) * 1000

        total_ms = (time.time() - start_total) * 1000
        logger.info(
            "Retrieval complete: backend=%s, candidates=%d, reranked=%d, "
            "total=%.1fms (rerank=%.1fms)",
            backend_used, len(fused), len(reranked), total_ms, rerank_ms
        )

        return reranked

    # ── PRIVATE HELPERS ───────────────────────────────────────────────────────

    def _retrieve_candidates(
        self,
        query: str,
        query_embedding: list[float],
        service_filter: Optional[str],
    ) -> tuple[list[SearchResult], list[SearchResult], str]:
        """
        Retrieve candidates from OpenSearch or fall back to FAISS.

        Returns:
            Tuple of (bm25_results, dense_results, backend_used).
            bm25_results is empty when using FAISS (no BM25 available).
        """
        if self._backend == BACKEND_OPENSEARCH:
            # Try OpenSearch first.
            if self._opensearch.is_healthy():
                try:
                    start = time.time()

                    # Run BM25 and KNN searches.
                    # Why sequential (not parallel): Python's GIL limits true
                    # parallelism for CPU-bound work. For I/O-bound OpenSearch
                    # calls, asyncio would help — but that requires async
                    # throughout the stack. Sequential is simpler and the
                    # latency difference is ~50ms at this scale.
                    bm25_results = self._opensearch.bm25_search(
                        query, k=CANDIDATES_PER_METHOD, service_filter=service_filter
                    )
                    dense_results = self._opensearch.knn_search(
                        query_embedding, k=CANDIDATES_PER_METHOD,
                        service_filter=service_filter
                    )

                    search_ms = (time.time() - start) * 1000
                    logger.debug(
                        "OpenSearch: BM25=%d, KNN=%d results in %.1fms",
                        len(bm25_results), len(dense_results), search_ms
                    )
                    return bm25_results, dense_results, BACKEND_OPENSEARCH

                except Exception as e:
                    logger.warning(
                        "OpenSearch search failed, falling back to FAISS: %s", e
                    )
                    # Fall through to FAISS fallback below.
            else:
                logger.warning("OpenSearch unhealthy, using FAISS fallback")

        # FAISS path — either backend="faiss" or OpenSearch unavailable.
        dense_results = self._faiss_search(query_embedding, service_filter)
        return [], dense_results, BACKEND_FAISS

    def _faiss_search(
        self,
        query_embedding: list[float],
        service_filter: Optional[str],
    ) -> list[SearchResult]:
        """
        Search the FAISS index, loading it from disk if not yet loaded.

        Why lazy load: the FAISS index file may not exist on first startup
        (before ingestion runs). Lazy loading means the retriever can be
        instantiated without the index file existing — it only fails when
        a query actually arrives and the index is needed.
        """
        if not self._faiss_loaded:
            try:
                self._faiss.load(self._faiss_index_path, self._faiss_metadata_path)
                self._faiss_loaded = True
            except RuntimeError as e:
                logger.error("FAISS index not available: %s", e)
                return []

        return self._faiss.search(
            query_embedding,
            k=CANDIDATES_PER_METHOD,
            service_filter=service_filter
        )
