# PURPOSE: Executes BM25 and KNN queries against OpenSearch Serverless and returns scored result lists
# CALLED BY: retrieval.retriever
# DEPENDS ON: opensearch-py, boto3 (AWS SigV4 auth), OPENSEARCH_ENDPOINT, OPENSEARCH_INDEX env vars

from __future__ import annotations

import logging
import os
from typing import Optional

from retrieval.faiss_fallback import SearchResult

logger = logging.getLogger(__name__)


# ─── CONFIGURATION ────────────────────────────────────────────────────────────

# Default number of candidates to retrieve from each search method.
# Why 40: we retrieve k*2 candidates before RRF fusion to account for
# post-filtering losses. If service_filter removes half the results,
# we still have 20 left for the reranker.
DEFAULT_CANDIDATES_K = 40


# ─── PUBLIC CLASS ─────────────────────────────────────────────────────────────

class OpenSearchClient:
    """
    Client for BM25 and KNN queries against OpenSearch Serverless.

    Why OpenSearch Serverless (not managed domain):
    - Pay per OCU consumed — ~$25 for intermittent use vs ~$70/month minimum
      for a managed domain
    - BM25 and KNN in the same query natively — no second system needed
    - Persistent across service restarts — index survives Lambda cold starts
    - Multi-instance sharing — all gateway instances query the same index

    Why SigV4 authentication:
    OpenSearch Serverless uses AWS SigV4 request signing for authentication,
    not username/password. Every HTTP request must be signed with the caller's
    AWS credentials. The opensearch-py library handles this via the
    RequestsHttpConnection with AWS4Auth.

    Why nmslib engine for KNN (not faiss engine):
    nmslib HNSW has better recall at equivalent latency for 1536-dim vectors
    at our corpus size. The faiss engine in OpenSearch is optimised for very
    large corpora (millions of vectors) where approximate methods matter more.

    NOTE: This class is implemented in Day 5 when OpenSearch Serverless is
    provisioned. The interface is defined here so retriever.py can reference
    it without circular imports.
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        index_name: Optional[str] = None,
        region: Optional[str] = None,
    ) -> None:
        """
        Initialise the OpenSearch client with SigV4 authentication.

        Args:
            endpoint: OpenSearch Serverless endpoint URL.
                      Defaults to OPENSEARCH_ENDPOINT env var.
            index_name: Index name to query.
                        Defaults to OPENSEARCH_INDEX env var.
            region: AWS region. Defaults to AWS_REGION env var.
        """
        self._endpoint = endpoint or os.getenv("OPENSEARCH_ENDPOINT", "")
        self._index = index_name or os.getenv("OPENSEARCH_INDEX", "runbooks-index")
        self._region = region or os.getenv("AWS_REGION", "us-east-1")

        # Why lazy client creation: the opensearch-py client makes a connection
        # attempt on instantiation. If OpenSearch is not yet provisioned (Days 0-4),
        # importing this module would fail. Lazy creation defers the connection
        # until the first actual query.
        self._client = None

    def _get_client(self):
        """
        Create and cache the OpenSearch client with SigV4 auth.

        Why cached (not recreated per query): creating the client involves
        setting up the HTTP connection pool. Recreating it per query adds
        ~50ms overhead and wastes connections.

        Why SigV4 (not basic auth): OpenSearch Serverless requires AWS
        request signing. Basic auth is not supported for Serverless collections.
        """
        if self._client is not None:
            return self._client

        # Why import here (not at module top): opensearch-py and boto3 are
        # heavy imports. Deferring them means this module can be imported
        # without triggering connection attempts during testing.
        from opensearchpy import OpenSearch, RequestsHttpConnection
        from requests_aws4auth import AWS4Auth
        import boto3

        # Get AWS credentials from the environment.
        # Why boto3.Session: automatically picks up credentials from environment
        # variables, ~/.aws/credentials, or IAM role (Lambda execution role).
        credentials = boto3.Session().get_credentials()
        aws_auth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            self._region,
            "aoss",                    # service name for OpenSearch Serverless
            session_token=credentials.token
        )

        self._client = OpenSearch(
            hosts=[{"host": self._endpoint.replace("https://", ""), "port": 443}],
            http_auth=aws_auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=30,
        )

        logger.info("OpenSearch client initialised for endpoint: %s", self._endpoint)
        return self._client

    def bm25_search(
        self,
        query: str,
        k: int = DEFAULT_CANDIDATES_K,
        service_filter: Optional[str] = None,
    ) -> list[SearchResult]:
        """
        Execute a BM25 full-text search against the chunk_text field.

        Why BM25 for runbooks: exact command matches like `systemctl restart payment-api`
        score very high in BM25 because the tokens match exactly. Dense search
        might not rank this as highly if the embedding model doesn't strongly
        associate the exact command string with the query.

        Args:
            query: The user's natural language query string.
            k: Number of results to return.
            service_filter: If set, add a bool filter for service_name.

        Returns:
            List of SearchResult sorted by BM25 score descending.

        Raises:
            RuntimeError: If the OpenSearch query fails.
        """
        try:
            client = self._get_client()

            # Build the OpenSearch query body.
            # Why match query on chunk_text: the chunk_text field has the
            # english analyzer applied, which handles stemming and stop words.
            # "restarting" matches "restart", "services" matches "service".
            query_body: dict = {
                "size": k,
                "query": {
                    "bool": {
                        "must": [
                            {
                                "match": {
                                    "chunk_text": {
                                        "query": query,
                                        "operator": "or",
                                        # Why operator=or: returns results that
                                        # match ANY query token. operator=and
                                        # would require ALL tokens to match,
                                        # which is too strict for natural language.
                                    }
                                }
                            }
                        ],
                        # Why filter (not must) for service_name: filter clauses
                        # don't affect the BM25 score — they just exclude non-matching
                        # documents. Using must would penalise the BM25 score for
                        # documents that don't contain the service_name in chunk_text.
                        "filter": _build_service_filter(service_filter)
                    }
                },
                "_source": [
                    "chunk_id", "chunk_text", "source_runbook", "section_name",
                    "page_num", "service_name", "team_owner", "severity_level"
                ]
            }

            response = client.search(index=self._index, body=query_body)
            return _parse_search_response(response)

        except Exception as e:
            raise RuntimeError(f"OpenSearch BM25 search failed: {e}") from e

    def knn_search(
        self,
        query_embedding: list[float],
        k: int = DEFAULT_CANDIDATES_K,
        service_filter: Optional[str] = None,
    ) -> list[SearchResult]:
        """
        Execute a KNN vector search against the embedding field.

        Why KNN for runbooks: semantic queries like "service won't start" don't
        contain the exact tokens from the runbook, but their embedding is
        semantically close to restart procedure chunks. BM25 would miss these.

        Why pre-filter (not post-filter) in OpenSearch:
        OpenSearch KNN supports native bool filters — the filter is applied
        BEFORE the vector search, reducing the candidate set. This is more
        efficient than FAISS post-filtering because OpenSearch doesn't waste
        time computing distances for documents that will be filtered out.

        Args:
            query_embedding: 1536-dim float list from embedder.py.
            k: Number of results to return.
            service_filter: If set, add a bool filter for service_name.

        Returns:
            List of SearchResult sorted by cosine similarity descending.

        Raises:
            RuntimeError: If the OpenSearch query fails.
        """
        try:
            client = self._get_client()

            # Build the KNN query body.
            # Why knn query type: this triggers OpenSearch's HNSW approximate
            # nearest neighbour search on the knn_vector field.
            query_body: dict = {
                "size": k,
                "query": {
                    "knn": {
                        "embedding": {
                            "vector": query_embedding,
                            "k": k,
                            # Why filter inside knn: OpenSearch supports pre-filtering
                            # within the knn query. This is more efficient than a
                            # post-filter because the HNSW graph traversal only
                            # considers documents that pass the filter.
                            "filter": _build_service_filter(service_filter) or {}
                        }
                    }
                },
                "_source": [
                    "chunk_id", "chunk_text", "source_runbook", "section_name",
                    "page_num", "service_name", "team_owner", "severity_level"
                ]
            }

            response = client.search(index=self._index, body=query_body)
            return _parse_search_response(response)

        except Exception as e:
            raise RuntimeError(f"OpenSearch KNN search failed: {e}") from e

    def is_healthy(self) -> bool:
        """
        Check if OpenSearch is reachable.

        Why needed: retriever.py uses this to decide whether to use OpenSearch
        or fall back to FAISS. A simple ping is faster than catching exceptions
        on every search call.

        Returns:
            True if OpenSearch responds to a cluster health check, False otherwise.
        """
        try:
            client = self._get_client()
            client.cluster.health()
            return True
        except Exception:
            return False


# ─── PRIVATE HELPERS ──────────────────────────────────────────────────────────

def _build_service_filter(service_filter: Optional[str]) -> list[dict]:
    """
    Build an OpenSearch bool filter clause for service_name.

    Why a separate function: both bm25_search and knn_search need this logic.
    One function, not two copies.

    Args:
        service_filter: service_name to filter by, or None for no filter.

    Returns:
        List of filter clauses (empty list = no filter applied).
    """
    if not service_filter:
        # Why empty list (not None): OpenSearch bool filter expects a list.
        # An empty list means "no filter" — all documents pass.
        return []

    return [
        {
            "term": {
                # Why keyword field (not text): service_name is mapped as
                # keyword type in the index. keyword fields support exact-match
                # term queries. text fields are analyzed (stemmed, lowercased)
                # and don't support exact-match filtering.
                "service_name": service_filter
            }
        }
    ]


def _parse_search_response(response: dict) -> list[SearchResult]:
    """
    Parse an OpenSearch search response into a list of SearchResult objects.

    Why a separate function: both bm25_search and knn_search return the same
    response structure. One parser, not two copies.

    Args:
        response: Raw OpenSearch search response dict.

    Returns:
        List of SearchResult, one per hit, in the order returned by OpenSearch.
    """
    results = []
    hits = response.get("hits", {}).get("hits", [])

    for hit in hits:
        source = hit.get("_source", {})
        # Why _score: OpenSearch puts the relevance score in _score, not in _source.
        score = hit.get("_score", 0.0)

        results.append(SearchResult(
            score=float(score) if score is not None else 0.0,
            chunk_id=source.get("chunk_id", ""),
            chunk_text=source.get("chunk_text", ""),
            source_runbook=source.get("source_runbook", ""),
            section_name=source.get("section_name", ""),
            page_num=source.get("page_num", 0),
            service_name=source.get("service_name", ""),
            team_owner=source.get("team_owner", ""),
            severity_level=source.get("severity_level", "unknown"),
        ))

    return results
