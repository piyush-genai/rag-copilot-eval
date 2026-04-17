# PURPOSE: Pydantic request/response types for the FastAPI gateway — QueryRequest, QueryResponse, Citation
# CALLED BY: gateway.query_handler, gateway.main (FastAPI route type hints)
# DEPENDS ON: pydantic

from pydantic import BaseModel, Field
from typing import Optional


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    service_filter: Optional[str] = Field(None, description="Filter results to a specific service name")
    top_k: int = Field(5, ge=1, le=20, description="Number of chunks to retrieve before reranking")


class Citation(BaseModel):
    source_runbook: str
    section_name: str
    page_num: int


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    latency_ms: float
    tokens_used: int
    route_info: dict  # e.g. {"backend": "opensearch", "bm25_ms": 12, "dense_ms": 34, "rerank_ms": 210}
