---
inclusion: always
---

# ENTERPRISE RAG COPILOT — 8-DAY BUILD PLAN
## Project 3 · Resume-Backed · Kiro-Integrated · Interview-Ready

**Repo:** `rag-copilot-eval` | **Owner:** Piyush Chaudhari
**Stack:** AWS Bedrock · OpenSearch Serverless · FAISS · FastAPI · LangChain · RAGAS · DeepEval · Lambda · pgvector
**Target:** Ship in 8 days. Understand everything. Real evaluation metrics only.
**Reference:** `jamwithai/production-agentic-rag-course` — open as reference tab, never copy-paste
**Domain:** Technical Operations Runbooks — 200+ documents covering incident response, deployment procedures, infra troubleshooting

**Resume Claim This Backs Up:** "Built a hybrid-search RAG system over 200+ technical runbooks using Bedrock embeddings, OpenSearch (BM25 + dense vector fusion), semantic chunking with sliding window overlap, and cross-encoder reranking — achieving context precision of 0.91 and answer relevancy of 0.88 on RAGAS evaluation. Automated evaluation pipeline using RAGAS and DeepEval — automated on every KB update via Lambda trigger, with regression gates blocking deployment if metrics drop more than 5%. Onboarding time for technical documentation reduced from 5 days to under 2.5 days."

---

## DUAL-TRACK DEVELOPMENT APPROACH (Non-negotiable for every day)

Every day that involves AWS infrastructure follows this split without exception:

| Track | What | Who does it |
|---|---|---|
| **AWS Console Track** | Creating infrastructure, configuring services, verifying in the console | Piyush manually — Kiro gives step-by-step instructions |
| **Code Track** | Writing Python, running terminal commands, tests, commits | Kiro writes, Piyush runs and reviews |

**Why this split exists:**
- Console work builds AWS muscle memory and interview talking points
- "I created the OpenSearch Serverless collection, configured the index mapping,
  and set up the data access policy" is a real answer. "A script did it" is not.
- Every AWS component Piyush creates manually, he can explain, recreate, and debug

**Kiro's responsibility on AWS days:**
1. Before any console work: explain what the component is and why it's needed in simple words
2. Give exact step-by-step console instructions (which service, which menu, which button, which exact value to type)
3. After console work: give terminal commands to verify it worked
4. Never skip the console step by writing a Terraform/CDK/boto3 script instead
5. If something fails in the console, diagnose it and explain why before suggesting a fix

**AWS components that must always be created manually in the console:**
- OpenSearch Serverless collection creation and index mapping
- IAM role and policy creation
- S3 bucket creation and event trigger configuration
- Lambda function deployment and trigger setup
- SNS topic and SSM Parameter creation
- Bedrock model access requests

---

## CANONICAL FOLDER STRUCTURE (Source of Truth)

> NOTE: The original 8-day plan used `api/`, `generation/`, and `eval_data/`. These were intentionally
> refactored in the Kiro scaffold. Do NOT add them back. The mapping is:
> - `api/` → `gateway/` (cleaner separation: routing vs. pipeline)
> - `generation/bedrock_generator.py` → `gateway/prompt_builder.py` + `gateway/sse_streamer.py` (prompt construction ≠ streaming)
> - `eval_data/qa_pairs.json` → `evaluation/data/golden_set.json` (organised under evaluation module)

```
rag-copilot-eval/
│
├── ingestion/
│   ├── pdf_extractor.py        # Extracts raw text page by page from PDF runbooks
│   ├── section_detector.py     # Identifies runbook sections: Overview, Prerequisites, Steps, Troubleshooting
│   ├── chunker.py              # Splits runbook text into overlapping semantic chunks
│   ├── metadata_tagger.py      # Attaches structured metadata to each chunk: service, severity, team
│   ├── metadata_schema.py      # Pydantic model for chunk metadata (chunk_id, source_runbook, etc.)
│   └── lambda_handler.py       # AWS Lambda entry point — triggered by S3 upload of new runbook
│
├── retrieval/
│   ├── retriever.py            # Orchestrates hybrid retrieval — calls search, fuses, reranks
│   ├── opensearch_client.py    # BM25 + KNN queries against OpenSearch Serverless
│   ├── faiss_fallback.py       # In-memory FAISS index — fallback when OpenSearch is unavailable
│   ├── rrf_fusion.py           # Reciprocal Rank Fusion (k=60) — merges BM25 + KNN result lists
│   └── reranker.py             # Cross-encoder reranker (MiniLM-L-6) — top-40 → top-5
│
├── gateway/                    # Replaces old api/ + generation/ folders
│   ├── main.py                 # FastAPI app — entry point, routes, middleware wiring
│   ├── models.py               # Pydantic types — QueryRequest, QueryResponse, Citation
│   ├── query_handler.py        # POST /query — validates input, calls retriever, invokes Claude
│   ├── prompt_builder.py       # Assembles system + user prompt with citations (replaces bedrock_generator)
│   ├── sse_streamer.py         # Wraps Bedrock streaming response as SSE (replaces bedrock_generator)
│   └── middleware.py           # Request ID, timing, structured JSON logging
│
├── evaluation/
│   ├── ragas_pipeline.py       # Runs RAGAS metrics: faithfulness, context_precision, answer_relevancy
│   ├── deepeval_tests.py       # DeepEval HallucinationMetric on all generated answers
│   ├── golden_dataset.py       # Loads and validates the golden Q&A test set
│   ├── regression_gate.py      # Lambda: runs eval on new KB upload, blocks deploy if metrics drop >5%
│   └── data/
│       ├── golden_set.json     # 40 ground-truth Q&A pairs (replaces eval_data/qa_pairs.json)
│       └── baseline_metrics.json  # Saved RAGAS scores — regression gate compares against these
│
├── infra/
│   ├── iam_policy.json         # Minimum IAM permissions for Lambda ingestion role
│   └── opensearch_index_config.json  # OpenSearch index mapping (KNN + BM25 fields)
│
├── data/
│   └── runbooks/               # Source runbook PDFs — gitignored, .gitkeep holds the directory
│
└── tests/
    ├── test_chunker.py
    ├── test_rrf_fusion.py
    ├── test_retriever.py
    └── test_gateway.py
```

**Critical separation:** `ingestion/` and `retrieval/` are completely independent. They communicate only through the vector store (FAISS/OpenSearch). This means retrieval logic can be improved without re-embedding all documents.

---

## THE KIRO CONTRACT

| Mode | When | Obligation |
|---|---|---|
| ✅ Scaffold | File structure, boilerplate, Lambda YAML, Pydantic models | Read every line. Add `# why:` above every non-obvious block. |
| ✅ Debug | Stuck >20 min on a non-concept error | Trace the fix after. Write what you missed. |
| ❌ Never | Chunking strategy decisions, RRF formula, RAGAS interpretation, regression gate logic | Piyush writes these. Always. |

**CRITICAL: No Summary Documents**
- After making fixes or changes, DO NOT create summary markdown files (e.g., THROTTLING_FIX.md, CHANGES.md, SUMMARY.md)
- Explain changes inline in code comments only
- If explanation is needed, provide it verbally in the response, not as a new file

## CODE STYLE STANDARD (enforced on every file Kiro writes)

Every file Kiro produces must follow the style of `ingestion/chunker.py`. This is non-negotiable.

**Required in every file:**
- Three-line header: `# PURPOSE`, `# CALLED BY`, `# DEPENDS ON`
- Section dividers using `# ─── SECTION NAME ───` with dashes
- Every parameter/constant gets a `# Why X:` comment explaining the value and what happens if you change it
- Every non-obvious line gets an inline `# Why:` comment
- Every function gets a full docstring with: what it does, Args, Returns, and at least one `Why` explanation
- Private helpers are grouped under `# ─── PRIVATE HELPERS ───` with a note that they are internal
- No magic numbers — every numeric constant is named and explained
- Edge cases are handled explicitly with a comment explaining why the edge case exists

**What "non-obvious" means:**
- Any regex → explain what it matches and why that pattern
- Any slice `[start:end]` → explain what the slice extracts
- Any `break` or `continue` → explain why the loop exits here
- Any `max()` or `min()` → explain what it's bounding and why
- Any `**dict` spread → explain what fields are being spread and why
- Any `//` integer division → explain the approximation being made

---

## AWS COST GUARD

| Service | Rule | Est. Cost |
|---|---|---|
| Local FAISS | Days 0–4: free, no AWS spend | $0 |
| Bedrock Titan Embeddings V2 | ~10K embedding calls across the project | ~$5 |
| Bedrock Claude 3 Sonnet | ~500 generation calls | ~$15 |
| OpenSearch Serverless | Spin up Day 5 only, delete after each session | ~$25 |
| Lambda + S3 | Lambda free tier covers this volume | ~$3 |
| **Total** | Delete OpenSearch after project | **~$51** |

---

## DAY-BY-DAY FOCUS

| Day | Focus | Key Outcome |
|---|---|---|
| 0 | Domain — runbooks, incident response | All 10 domain questions answered in writing |
| 1 | Architecture + scaffold + AWS bootstrap | Repo structure with docstrings, S3 bucket with corpus |
| 2 | PDF extraction + section detection + chunking | 3000+ chunks committed with metadata |
| 3 | Bedrock embeddings + FAISS vector store | FAISS index built, 5-query retrieval test done |
| 4 | BM25 + hybrid search + RRF | Hybrid vs dense comparison committed |
| 5 | OpenSearch Serverless integration | OpenSearch indexed, toggle working |
| 6 | Bedrock generation + RAGAS + DeepEval | Baseline metrics saved to S3 |
| 7 | Reranker + FastAPI + Lambda regression gate | Gate tested, SSM parameter verified |
| 8 | README + interview simulation | Zero failures on interview simulation |

---

## KEY DESIGN DECISIONS (Never Deviate Without Reason)

- Chunking: section-aware sliding window, 400 token max, 30 token overlap, never span section boundaries
- Embeddings: Bedrock Titan Embeddings V2, 1536-dim, L2-normalised before FAISS IndexFlatIP
- Retrieval: BM25 (rank_bm25 via opensearch_client/faiss_fallback) + dense KNN, k*2 candidates each, RRF fusion k=60 (rrf_fusion.py), top-40 → reranker → top-5
- Reranker: cross-encoder/ms-marco-MiniLM-L-6-v2 on CPU
- Generation: Claude 3 Sonnet via gateway/query_handler.py, prompt assembled in prompt_builder.py, streamed via sse_streamer.py, citations mandatory, no command paraphrasing
- Evaluation: RAGAS (ragas_pipeline.py) + DeepEval (deepeval_tests.py) + HallucinationMetric, ground truth in evaluation/data/golden_set.json, baseline in evaluation/data/baseline_metrics.json
- Regression gate: >5% drop on any metric → SNS alert + SSM Parameter BLOCKED
- Target metrics: context_precision ≥ 0.88, answer_relevancy ≥ 0.85, faithfulness ≥ 0.90

---

## PIVOT TRIGGERS

| Trigger | Action |
|---|---|
| OpenSearch Serverless quota denied | Complete on FAISS only. Document OpenSearch as intended production path. |
| RAGAS scores won't reach targets | Document honest achieved scores with analysis. Real 0.78 with understanding beats fake 0.91. |
| Lambda regression gate cold start issues | Switch to Step Functions with warmup. Document the change. |
| AWS spend > $70 by Day 6 | Kill OpenSearch Serverless, finish on FAISS, document cost trade-off. |
| Interview opportunity before Day 8 | Stop. Go to interview with what you have. |
