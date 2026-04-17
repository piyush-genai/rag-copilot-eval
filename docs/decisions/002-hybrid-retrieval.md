# Decision 002 — Hybrid Retrieval with RRF Fusion

**Date:** 2026-04-17  
**Status:** Accepted  
**Component:** `retrieval/retriever.py`, `retrieval/rrf_fusion.py`, `retrieval/opensearch_client.py`

---

## Context

Runbook queries fall into two distinct patterns:

1. **Symptom queries** — "payment service returning 503" — require semantic understanding
2. **Exact-term queries** — "systemctl restart payment-api" — require keyword matching

A single retrieval method handles one pattern well and the other poorly.

---

## Decision

**BM25 + dense KNN hybrid retrieval, fused with Reciprocal Rank Fusion (k=60).**

Both methods retrieve `k*2` candidates independently. RRF merges the two ranked lists into a single unified ranking. The top-40 fused results are passed to the cross-encoder reranker, which returns top-5 for generation.

RRF formula: `score(d) = Σ 1 / (k + rank_i(d))` where k=60.

---

## Why RRF Over Score Averaging

BM25 scores range from 0 to 15+. Cosine similarity scores range from 0 to 1. Direct averaging lets BM25 dominate regardless of semantic relevance. RRF uses only rank positions — it is scale-agnostic. A document ranked #1 in BM25 and #8 in dense gets the same RRF score as a document ranked #4 in both — both are consistently relevant.

k=60 is empirically established as the standard default. Low k (e.g. 5) over-weights rank 1. High k (e.g. 200) flattens all ranks to near-equal scores.

---

## Why a Two-Stage Pipeline (Hybrid → Cross-Encoder)

The cross-encoder attends to every token in both the query and the candidate chunk simultaneously — significantly more accurate than bi-encoder similarity. But it cannot be precomputed and runs at query time, making it too slow for thousands of candidates.

The pipeline separates concerns: hybrid search provides fast broad recall (top-40), cross-encoder provides accurate precision (top-5). Neither stage alone achieves both.

---

## Alternatives Considered

| Approach | Reason Rejected |
|---|---|
| Dense-only retrieval | Misses exact command matches. "systemctl restart payment-api" in a query may not semantically match the chunk containing that exact command. |
| BM25-only retrieval | Misses paraphrased queries. "service won't start" does not keyword-match "systemctl restart". |
| Score averaging for fusion | BM25 score scale dominates. Produces worse results than RRF on mixed query types. |
| Cross-encoder on all candidates | Too slow at query time. 200 candidates × 200ms per pair = 40 seconds. Unacceptable for incident response. |

---

## Consequences

- Retrieval handles both exact-term and semantic queries without tuning per query type
- FAISS fallback (dense-only, no BM25) is available when OpenSearch is unavailable — recall degrades but the system remains functional
- RRF k=60 is a fixed parameter. If retrieval quality degrades on a specific query type, k is the first parameter to tune
- The two-stage pipeline adds ~200ms reranking latency — acceptable for the target p95 of under 4 seconds to first token
