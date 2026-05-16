# RAG System Architecture Spec — Enterprise Technical Runbooks

---

## 1. Component Responsibilities

| Component | What it does |
|---|---|
| S3 | Durable object store for raw PDF runbooks, versioned by `last_modified` timestamp |
| Lambda (ingestion trigger) | Reacts to S3 `ObjectCreated` events, orchestrates the full ingestion pipeline |
| PDF extraction | Parses raw bytes into structured text, preserving page numbers and layout signals |
| Section detection | Identifies logical boundaries (headings, numbered steps) to split docs into coherent units |
| Semantic chunking + overlap | Splits sections into token-bounded chunks with sliding overlap to preserve cross-boundary context |
| Bedrock Titan Embeddings V2 | Converts chunk text into 1536-dim dense vectors for semantic similarity search |
| OpenSearch Serverless | Hosts both BM25 (keyword) and KNN (dense) indexes for hybrid retrieval at query time |
| FAISS local fallback | In-memory vector store inside Lambda that serves queries if OpenSearch is unavailable |
| BM25 + dense fusion (RRF) | Combines keyword and semantic result lists using Reciprocal Rank Fusion to produce a unified ranked set |
| Cross-encoder reranker | Re-scores the fused top-k candidates with a more expensive pairwise relevance model |
| Bedrock Claude 3 Sonnet | Generates the final grounded answer from reranked context chunks via a structured prompt |
| FastAPI async gateway | Exposes the query endpoint, manages SSE streaming of Claude's token output to the client |
| RAGAS pipeline | Evaluates `context_precision`, `faithfulness`, and `answer_relevancy` on a golden test set |
| Regression gate Lambda | Blocks deployment if any RAGAS metric degrades beyond threshold vs. baseline |

---

## 2. Failure Modes

| Component | What breaks |
|---|---|
| S3 | Runbooks unavailable; ingestion pipeline starved; no new content indexed |
| Lambda (ingestion) | New/updated runbooks silently not indexed; stale data served to engineers |
| PDF extraction | Garbled or empty chunk text; embeddings encode noise; retrieval quality collapses |
| Section detection | Chunks span multiple unrelated procedures; context bleeds across topics |
| Semantic chunking | Chunks too large → exceed context window; too small → lose procedural coherence |
| Titan Embeddings V2 | Ingestion halts; no vectors written; existing index goes stale on updates |
| OpenSearch Serverless | Primary retrieval path down; system falls back to FAISS (degraded recall) |
| FAISS fallback | If OpenSearch is also down, zero retrieval; Claude answers from parametric memory only (hallucination risk) |
| RRF fusion | Keyword-only or dense-only results; precision drops for ambiguous incident queries |
| Cross-encoder reranker | Top-k passed to Claude is noisier; answer quality degrades, especially for multi-step procedures |
| Claude 3 Sonnet | No answer generated; SSE stream never opens; engineer gets no response during incident |
| FastAPI gateway | All queries fail; engineers fall back to manual runbook search (defeats the system's purpose) |
| RAGAS pipeline | No quality signal; regressions ship silently |
| Regression gate Lambda | Bad deployments reach production undetected; context_precision degrades without alert |

---

## 3. Chunk Metadata Schema

```json
{
  "chunk_id": "string — SHA-256(source_runbook + section_name + chunk_index)",
  "source_runbook": "string — S3 object key, e.g. 'runbooks/payments/db-failover-v3.pdf'",
  "section_name": "string — detected heading, e.g. 'Step 4: Promote Read Replica'",
  "page_num": "integer — 1-indexed page in source PDF",
  "service_name": "string — owning service, e.g. 'payments-api'",
  "team_owner": "string — on-call team slug, e.g. 'platform-reliability'",
  "severity_level": "enum — ['P1','P2','P3','P4'] — incident severity this runbook targets",
  "last_updated": "ISO 8601 string — S3 LastModified of source object",
  "chunk_text": "string — raw text of this chunk, max ~512 tokens",
  "embedding": "float32[1536] — Titan Embeddings V2 dense vector"
}
```

Notes:
- `chunk_id` is deterministic so re-ingestion is idempotent (upsert, not duplicate insert)
- `severity_level` enables pre-filtering in OpenSearch before KNN to reduce noise for P1 incidents
- `embedding` is stored in OpenSearch KNN field; excluded from FAISS index metadata (stored separately)

---

## 4. IAM Permission Boundary — Lambda Ingestion Role

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadSourceRunbooks",
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:GetObjectVersion"],
      "Resource": "arn:aws:s3:::runbooks-bucket/*"
    },
    {
      "Sid": "ListBucketForTriggerValidation",
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": "arn:aws:s3:::runbooks-bucket"
    },
    {
      "Sid": "InvokeEmbeddingModel",
      "Effect": "Allow",
      "Action": ["bedrock:InvokeModel"],
      "Resource": "arn:aws:bedrock:*::foundation-model/amazon.titan-embed-text-v2:0"
    },
    {
      "Sid": "WriteToOpenSearch",
      "Effect": "Allow",
      "Action": ["aoss:APIAccessAll"],
      "Resource": "arn:aws:aoss:REGION:ACCOUNT:collection/runbooks-index"
    },
    {
      "Sid": "WriteLogs",
      "Effect": "Allow",
      "Action": ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
      "Resource": "arn:aws:logs:REGION:ACCOUNT:log-group:/aws/lambda/runbook-ingestion:*"
    },
    {
      "Sid": "ReadEncryptionKey",
      "Effect": "Allow",
      "Action": ["kms:Decrypt", "kms:GenerateDataKey"],
      "Resource": "arn:aws:kms:REGION:ACCOUNT:key/YOUR_KEY_ID"
    }
  ]
}
```

Explicitly denied (not granted): `s3:PutObject`, `s3:DeleteObject`, `bedrock:InvokeModel` on Claude (ingestion role has no query path access), any IAM/STS actions.

---

## 5. Data Flow Diagram — One Query, Input to Response

```
Engineer types query: "How do I promote the read replica in payments DB failover?"
│
▼
[FastAPI async gateway]
  - Validates request, extracts query string
  - Opens SSE stream to client
  - Calls retrieval service async
│
▼
[Query Embedding]
  - Calls Bedrock Titan Embeddings V2
  - Returns query_vector: float32[1536]
│
▼
[Hybrid Retrieval — OpenSearch Serverless]
  ├── BM25 search: keyword match on chunk_text
  │     → top-20 results with BM25 scores
  └── KNN search: ANN on embedding field vs query_vector
        → top-20 results with cosine similarity scores
  [If OpenSearch unavailable → FAISS local fallback, dense-only]
│
▼
[RRF Fusion]
  - Merges BM25 list + KNN list using Reciprocal Rank Fusion
  - score_rrf(d) = Σ 1/(k + rank_i(d)), k=60
  - Produces unified top-40 ranked chunks
│
▼
[Cross-Encoder Reranker]
  - Scores each of top-40 chunks against query with pairwise model
  - Re-ranks, selects top-5 chunks
│
▼
[Prompt Assembly]
  - System prompt: "You are an on-call assistant. Answer only from provided context."
  - Context: top-5 chunk_text blocks with section_name + source_runbook citations
  - User turn: original query
│
▼
[Bedrock Claude 3 Sonnet — streaming]
  - Generates grounded step-by-step answer
  - Streams tokens back via InvokeModelWithResponseStream
│
▼
[FastAPI SSE stream]
  - Forwards token chunks to engineer's client in real time
  - Appends citations: [source_runbook, section_name, page_num] at end of stream
│
▼
Engineer sees: exact procedural steps with source attribution, ~2-4s to first token
```

---

## Notes

- The FAISS fallback will have recall gaps vs OpenSearch KNN because it won't have BM25. Log fallback events to measure frequency.
- Pin your RAGAS golden set to real P1 incident queries — synthetic questions won't catch the precision drops that matter most to on-call engineers.
- The `severity_level` pre-filter on OpenSearch is a high-leverage optimization; during a P1 incident you don't want P4 runbook chunks diluting your top-k.
