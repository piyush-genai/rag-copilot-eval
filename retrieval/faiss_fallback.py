# PURPOSE: In-memory FAISS index that serves dense-only retrieval when OpenSearch is unavailable
# CALLED BY: retrieval.retriever (on OpenSearch connection failure)
# DEPENDS ON: faiss-cpu, numpy, local .faiss index file path

from __future__ import annotations

import json
import logging
import os
import pickle
from dataclasses import dataclass, field
from typing import Optional

import faiss
import numpy as np

logger = logging.getLogger(__name__)


# ─── CONFIGURATION ────────────────────────────────────────────────────────────

# Titan Embeddings V2 produces 1536-dimensional vectors.
# Why this constant: FAISS index must be created with the exact same dimension
# as the vectors it will store. Mismatch causes a runtime error.
EMBEDDING_DIM = 1536

# Default paths for persisting the FAISS index and metadata to disk.
# Why separate files: FAISS stores only the raw float vectors — it has no
# concept of metadata (chunk_id, source_runbook, etc.). We store metadata
# in a parallel pickle file, keyed by the same integer index position.
DEFAULT_INDEX_PATH = "data/faiss_index.bin"
DEFAULT_METADATA_PATH = "data/faiss_metadata.pkl"


# ─── DATA STRUCTURES ──────────────────────────────────────────────────────────

@dataclass
class SearchResult:
    """
    One result returned by a similarity search.

    Why a dataclass (not a plain dict): type hints make it clear what fields
    are available. The retriever and reranker can rely on these fields existing.
    """
    score: float            # cosine similarity score (0.0 to 1.0, higher = more similar)
    chunk_id: str           # deterministic ID from chunker.py
    chunk_text: str         # the actual text content of this chunk
    source_runbook: str     # S3 key of the source PDF
    section_name: str       # section heading this chunk came from
    page_num: int           # page where this chunk's section begins
    service_name: str       # extracted from filename, "" if unknown
    team_owner: str         # "" until enriched
    severity_level: str     # "P1"|"P2"|"P3"|"P4"|"unknown"


# ─── PUBLIC CLASS ─────────────────────────────────────────────────────────────

class FAISSVectorStore:
    """
    In-memory FAISS vector store for dense similarity search.

    Why FAISS for local development (Days 0-4):
    - Runs in-process, no infrastructure needed
    - Free — no AWS spend during development
    - Same retrieval concepts as OpenSearch KNN (cosine similarity, top-k)
    - Switching to OpenSearch on Day 5 requires only changing the backend
      parameter in HybridSearcher — not the retrieval logic

    Why IndexFlatIP (inner product):
    - When vectors are L2-normalised (magnitude = 1), inner product equals
      cosine similarity. This is the standard approach for text embeddings.
    - "Flat" means exhaustive search — checks every vector. Accurate but
      slower than approximate methods (IVF, HNSW) at large scale.
    - For 3000 chunks (our corpus), exhaustive search takes ~5ms. Fast enough.
    - At 300,000 chunks, switch to IndexIVFFlat or use OpenSearch HNSW.

    Limitations vs OpenSearch:
    - No BM25 — dense-only retrieval. Exact-term queries have degraded recall.
    - No persistence across service restarts (unless save/load is called).
    - No multi-instance sharing — each process has its own in-memory index.
    """

    def __init__(self) -> None:
        # Create the FAISS index.
        # IndexFlatIP = inner product (cosine similarity on normalised vectors).
        self._index: faiss.IndexFlatIP = faiss.IndexFlatIP(EMBEDDING_DIM)

        # Parallel metadata store: integer position → metadata dict.
        # Why a list (not a dict): FAISS returns integer indices (0, 1, 2...).
        # A list gives O(1) lookup by position. A dict would work too but
        # adds unnecessary key hashing overhead.
        self._metadata: list[dict] = []

    # ── PUBLIC METHODS ────────────────────────────────────────────────────────

    def add_chunks(self, chunks: list[dict]) -> None:
        """
        Add embedded chunks to the FAISS index.

        Each chunk must have an "embedding" field (list of 1536 floats).
        All other fields (chunk_id, chunk_text, source_runbook, etc.) are
        stored in the parallel metadata list.

        Args:
            chunks: List of chunk dicts from embedder.py. Must have "embedding".

        Raises:
            RuntimeError: If a chunk is missing its embedding or has wrong dimension.
        """
        if not chunks:
            # Edge case: nothing to add. Return silently.
            return

        # Validate and collect embeddings.
        vectors = []
        for i, chunk in enumerate(chunks):
            embedding = chunk.get("embedding")

            # Why validate here: a missing embedding means embedder.py failed
            # silently. Catching it here prevents a cryptic FAISS error later.
            if not embedding:
                raise RuntimeError(
                    f"Chunk at index {i} (chunk_id={chunk.get('chunk_id')}) "
                    f"has no embedding. Run embed_chunks() before add_chunks()."
                )

            if len(embedding) != EMBEDDING_DIM:
                raise RuntimeError(
                    f"Chunk {chunk.get('chunk_id')} has embedding dimension "
                    f"{len(embedding)}, expected {EMBEDDING_DIM}."
                )

            vectors.append(embedding)

        # Convert to numpy float32 array.
        # Why float32: FAISS requires float32. Python floats are float64 by default.
        # Converting here avoids a silent precision loss inside FAISS.
        vectors_np = np.array(vectors, dtype=np.float32)

        # L2-normalise all vectors before adding to the index.
        # Why normalise: IndexFlatIP computes inner product. For normalised vectors
        # (magnitude = 1), inner product = cosine similarity. Without normalisation,
        # longer vectors (from longer text) would score higher regardless of relevance.
        faiss.normalize_L2(vectors_np)

        # Add to the FAISS index.
        # Why add (not add_with_ids): IndexFlatIP assigns sequential integer IDs
        # automatically (0, 1, 2...). We use these as indices into self._metadata.
        self._index.add(vectors_np)

        # Store metadata in the parallel list.
        # Why exclude "embedding": the vector is already in FAISS. Storing it
        # again in metadata would double memory usage for no benefit.
        for chunk in chunks:
            self._metadata.append({
                k: v for k, v in chunk.items() if k != "embedding"
            })

        logger.info("Added %d chunks to FAISS index (total: %d)", len(chunks), self._index.ntotal)

    def search(
        self,
        query_embedding: list[float],
        k: int = 20,
        service_filter: Optional[str] = None,
    ) -> list[SearchResult]:
        """
        Find the top-k most similar chunks to a query embedding.

        Why post-filtering (not pre-filtering):
        FAISS does not support native metadata filters. We retrieve k*2 candidates
        from FAISS, then filter by service_name afterward. This means we may return
        fewer than k results if many candidates are filtered out.
        Trade-off: at our corpus size (3000 chunks), retrieving k*2=40 candidates
        and filtering is fast. At 300,000 chunks, pre-filtering via OpenSearch's
        bool filter is more efficient.

        Args:
            query_embedding: 1536-dim float list from embedder.py.
            k: Number of results to return after filtering.
            service_filter: If set, only return chunks from this service_name.

        Returns:
            List of SearchResult, sorted by score descending (best match first).

        Raises:
            RuntimeError: If the index is empty or query has wrong dimension.
        """
        if self._index.ntotal == 0:
            logger.warning("FAISS index is empty — no chunks have been added yet")
            return []

        if len(query_embedding) != EMBEDDING_DIM:
            raise RuntimeError(
                f"Query embedding has dimension {len(query_embedding)}, "
                f"expected {EMBEDDING_DIM}."
            )

        # Convert query to numpy float32 and normalise.
        # Why normalise: same reason as in add_chunks — inner product on
        # normalised vectors = cosine similarity.
        query_np = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_np)

        # Retrieve k*2 candidates to account for post-filtering losses.
        # Why k*2: if service_filter removes half the results, we still have k left.
        # If no filter is applied, we trim to k after retrieval.
        candidates_k = min(k * 2, self._index.ntotal)

        # FAISS search returns (distances, indices).
        # distances: cosine similarity scores (float32 array, shape [1, candidates_k])
        # indices: integer positions in self._metadata (int64 array, shape [1, candidates_k])
        distances, indices = self._index.search(query_np, candidates_k)

        # Build SearchResult objects from the raw FAISS output.
        results = []
        for score, idx in zip(distances[0], indices[0]):
            # Why check idx >= 0: FAISS returns -1 for padding when fewer than
            # candidates_k results exist in the index.
            if idx < 0:
                continue

            meta = self._metadata[idx]

            # Apply service_name post-filter if requested.
            if service_filter and meta.get("service_name") != service_filter:
                continue

            results.append(SearchResult(
                score=float(score),
                chunk_id=meta.get("chunk_id", ""),
                chunk_text=meta.get("text", ""),
                source_runbook=meta.get("source_runbook", ""),
                section_name=meta.get("section_name", ""),
                page_num=meta.get("page_num", 0),
                service_name=meta.get("service_name", ""),
                team_owner=meta.get("team_owner", ""),
                severity_level=meta.get("severity_level", "unknown"),
            ))

            # Stop once we have k results.
            if len(results) >= k:
                break

        return results

    def save(self, index_path: str = DEFAULT_INDEX_PATH, metadata_path: str = DEFAULT_METADATA_PATH) -> None:
        """
        Persist the FAISS index and metadata to disk.

        Why two files: FAISS can only save its vector index (binary format).
        Metadata (chunk_id, text, source_runbook, etc.) must be saved separately.
        We use pickle for metadata — fast and simple for local development.

        Args:
            index_path: Path to write the FAISS binary index file.
            metadata_path: Path to write the metadata pickle file.
        """
        # Create parent directories if they don't exist.
        os.makedirs(os.path.dirname(index_path) or ".", exist_ok=True)

        faiss.write_index(self._index, index_path)

        with open(metadata_path, "wb") as f:
            pickle.dump(self._metadata, f)

        logger.info(
            "Saved FAISS index (%d vectors) to %s and metadata to %s",
            self._index.ntotal, index_path, metadata_path
        )

    def load(self, index_path: str = DEFAULT_INDEX_PATH, metadata_path: str = DEFAULT_METADATA_PATH) -> None:
        """
        Load a previously saved FAISS index and metadata from disk.

        Why load (not rebuild): embedding 3000 chunks takes ~5 minutes and
        costs ~$0.50 in Bedrock API calls. Loading from disk takes <1 second.
        Always save after ingestion and load on service startup.

        Args:
            index_path: Path to the FAISS binary index file.
            metadata_path: Path to the metadata pickle file.

        Raises:
            RuntimeError: If either file does not exist.
        """
        if not os.path.exists(index_path):
            raise RuntimeError(
                f"FAISS index file not found: {index_path}. "
                f"Run the ingestion pipeline first to build the index."
            )
        if not os.path.exists(metadata_path):
            raise RuntimeError(
                f"FAISS metadata file not found: {metadata_path}. "
                f"Run the ingestion pipeline first to build the index."
            )

        self._index = faiss.read_index(index_path)

        with open(metadata_path, "rb") as f:
            self._metadata = pickle.load(f)

        logger.info(
            "Loaded FAISS index (%d vectors) from %s",
            self._index.ntotal, index_path
        )

    @property
    def total_vectors(self) -> int:
        """Return the number of vectors currently in the index."""
        return self._index.ntotal
