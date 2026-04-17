# PURPOSE: Orchestrates hybrid retrieval — calls OpenSearch (or FAISS fallback), fuses results, reranks
# CALLED BY: gateway.query_handler
# DEPENDS ON: retrieval.opensearch_client, retrieval.faiss_fallback, retrieval.rrf_fusion, retrieval.reranker
