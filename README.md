# PURPOSE: Project overview, setup instructions, and architecture summary
# CALLED BY: Developers onboarding to the project
# DEPENDS ON: Nothing

# rag-copilot-eval

RAG system for enterprise technical runbooks. Reduces on-call engineer onboarding from 5 days to 2.5 days.

## Stack

- Ingestion: S3 → Lambda → pdfplumber → Bedrock Titan Embeddings V2 → OpenSearch Serverless
- Retrieval: BM25 + KNN hybrid → RRF fusion → cross-encoder reranking
- Generation: Bedrock Claude 3 Sonnet via FastAPI SSE gateway
- Evaluation: RAGAS + DeepEval with regression gate

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # fill in your values
```

## Project Structure

```
rag-copilot-eval/
├── ingestion/       # PDF extraction, chunking, embedding, index writes
├── retrieval/       # Hybrid search, RRF fusion, reranking
├── gateway/         # FastAPI SSE query endpoint
├── evaluation/      # RAGAS pipeline and regression gate
├── infra/           # IAM, OpenSearch index config
└── tests/           # Unit and integration tests
```
