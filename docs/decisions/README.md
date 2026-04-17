# Architecture Decision Records

This directory documents the key technical decisions made during the design and implementation of this system. Each record captures the context, the decision, the alternatives that were considered, and the consequences.

| # | Decision | Status |
|---|---|---|
| [001](001-chunking-strategy.md) | Chunking Strategy — Section-aware sliding window | Accepted |
| [002](002-hybrid-retrieval.md) | Hybrid Retrieval — BM25 + dense KNN with RRF fusion | Accepted |
| [003](003-evaluation-and-regression-gate.md) | Evaluation Pipeline and Regression Gate | Accepted |
| [004](004-metadata-schema-design.md) | Chunk Metadata Schema Design | Accepted |
| [005](005-vector-store-and-fallback.md) | Vector Store — OpenSearch Serverless with FAISS fallback | Accepted |

## Format

Each record follows this structure:

- **Context** — what problem or constraint prompted this decision
- **Decision** — what was chosen and the key parameters
- **Alternatives Considered** — what else was evaluated and why it was rejected
- **Consequences** — what this decision enables and what it constrains

New decisions are added as numbered files (`006-...`) when a significant architectural choice is made.
