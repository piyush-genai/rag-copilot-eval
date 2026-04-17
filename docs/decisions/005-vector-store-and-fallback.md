# Decision 005 — Vector Store: OpenSearch Serverless with FAISS Fallback

**Date:** 2026-04-17  
**Status:** Accepted  
**Component:** `retrieval/opensearch_client.py`, `retrieval/faiss_fallback.py`

---

## Context

The retrieval layer needs a vector store that supports both BM25 (keyword) and KNN (dense) search in a single query, persists across service restarts, and scales to multiple application instances. A local fallback is needed for development and for resilience during OpenSearch outages.

---

## Decision

**OpenSearch Serverless as the primary vector store. FAISS in-memory index as the fallback.**

OpenSearch Serverless is used from Day 5 onward. FAISS is used for Days 0-4 (local development, no AWS spend) and as a runtime fallback when OpenSearch is unreachable.

---

## Why OpenSearch Serverless Over a Managed OpenSearch Domain

| Concern | Managed Domain | Serverless |
|---|---|---|
| Minimum cost | ~$70/month (always-on instances) | ~$25 for intermittent use (pay per OCU consumed) |
| BM25 + KNN in one query | Yes | Yes |
| Persistence | Yes | Yes |
| Multi-instance sharing | Yes | Yes |
| Cold start | None | Seconds on first request after idle |

For a portfolio project with intermittent traffic, Serverless is significantly cheaper. The cold start on first request is acceptable — this system is not latency-sensitive at the millisecond level.

---

## Why FAISS for Local Development (Not a Local OpenSearch Instance)

Running OpenSearch locally requires Docker and ~4GB RAM. FAISS runs in-process with no infrastructure. For Days 0-4 (embedding quality testing, chunking validation, retrieval logic development), FAISS provides all necessary functionality. The `VectorStore` interface is identical — switching to OpenSearch on Day 5 requires only changing the backend parameter, not the retrieval logic.

---

## FAISS Fallback Limitations

The FAISS fallback is dense-only — it does not have BM25. When the fallback is active:
- Exact-term queries (e.g. `systemctl restart payment-api`) have degraded recall
- RRF fusion is not possible — only dense ranking is returned

Every fallback activation is logged with a structured event so the frequency can be measured. If the fallback is triggered frequently in production, it indicates an OpenSearch availability issue that needs investigation — not a reason to expand the fallback's capabilities.

---

## Index Configuration

OpenSearch index mapping:
- `chunk_text`: `text` type with `english` analyzer (BM25)
- `embedding`: `knn_vector`, dimension 1536, HNSW with `nmslib` engine, `cosinesimil` space
- All metadata fields: `keyword` type (exact-match filtering, not full-text search)

`nmslib` engine is used over `faiss` engine in OpenSearch because `nmslib` HNSW has better recall at equivalent latency for this vector dimension and corpus size.

---

## Consequences

- The `HybridSearcher` backend toggle (`faiss` | `opensearch`) must be set correctly in the environment. Wrong setting silently degrades retrieval quality without errors.
- FAISS index must be rebuilt on every service restart (no persistence). For development this is acceptable. For production, OpenSearch is always the primary.
- OpenSearch Serverless must be deleted after each development session to avoid unnecessary cost. The index configuration in `infra/opensearch_index_config.json` allows it to be recreated in under 5 minutes.
