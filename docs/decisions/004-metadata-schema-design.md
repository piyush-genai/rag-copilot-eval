# Decision 004 — Chunk Metadata Schema Design

**Date:** 2026-04-17  
**Status:** Accepted  
**Component:** `ingestion/metadata_schema.py`

---

## Context

Every chunk stored in OpenSearch carries metadata fields used for pre-filtering before vector search. The schema must be defined at ingestion time — metadata extracted at query time adds latency and loses access to the full document context.

---

## Decision

**Pydantic `BaseModel` (not dataclass) with validation. Metadata tagged at ingestion time from filename, folder structure, and document content.**

Key schema fields and their rationale:

| Field | Type | Rationale |
|---|---|---|
| `chunk_id` | `str` | SHA-256(source + section + index)[:16]. Deterministic — enables upsert on re-ingestion. |
| `severity_level` | `str` | `"P1"\|"P2"\|"P3"\|"P4"\|"unknown"`. Defaults to `"unknown"`, not `"P3"`. |
| `embedding` | `list[float]` | Empty `[]` at schema creation. Populated by `embedder.py`. |
| `last_updated` | `str` | ISO 8601 from S3 `LastModified`. Empty string if unavailable. |

---

## Why Pydantic BaseModel Over Dataclass

Pydantic validates field types at instantiation. A `chunk_id` that is accidentally set to `None` raises a `ValidationError` immediately at ingestion time — not silently stored as `null` in OpenSearch where it would cause query failures later. For a schema that flows through multiple pipeline stages (ingestion → embedding → indexing → retrieval), validation at the boundary is worth the overhead.

---

## Why `severity_level` Defaults to `"unknown"` Not `"P3"`

OpenSearch pre-filters by `severity_level` before KNN search. A P1 emergency runbook silently labelled `"P3"` would be excluded from P1-filtered queries — exactly during the incidents where it is most needed. `"unknown"` is an explicit signal that enrichment has not occurred. `"P3"` is a false assertion of known severity.

Severity enrichment is a planned future enhancement (filename pattern matching, header keyword extraction). Until that is implemented, `"unknown"` is the correct default.

---

## Why Deterministic chunk_id (SHA-256) Not UUID

Re-ingesting the same runbook after an update must produce the same chunk IDs for unchanged chunks. `index_writer.py` uses these IDs to upsert — update if exists, insert if new. UUID-based IDs would create duplicate chunks on every re-ingest, growing the index unboundedly and degrading retrieval quality over time.

SHA-256 truncated to 16 hex characters (64 bits) is collision-resistant at the scale of millions of chunks. Full SHA-256 (64 characters) wastes storage across millions of OpenSearch documents without adding meaningful collision resistance at this scale.

---

## Why Metadata Is Tagged at Ingestion Time

At ingestion time, the full document context is available: filename, folder path, parent section heading, document header. `service_name = "payments-api"` extracted from `payments-api-restart-runbook.pdf` is more reliable than extracting it from a chunk of text that may say "the API" without naming it.

At query time, metadata extraction would add 50-300ms per candidate chunk. Across 40 candidates, that is 2-12 seconds added to every response — unacceptable for incident response use.

---

## Consequences

- `team_owner` is always `""` at ingestion — no reliable extraction signal exists in the current corpus. This field is reserved for future enrichment via a runbook registry or filename convention.
- `last_updated` requires the S3 `LastModified` timestamp to be passed through from the Lambda event. If the file is ingested from a local path (development mode), this field is empty.
- The `from_section` classmethod is the canonical way to construct a `ChunkMetadata` — direct instantiation is valid but bypasses the service name extraction and chunk ID generation logic.
