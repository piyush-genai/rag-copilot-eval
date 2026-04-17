# PURPOSE: Upserts chunk metadata and embeddings into OpenSearch Serverless KNN + BM25 indexes
# CALLED BY: ingestion.lambda_handler
# DEPENDS ON: opensearch-py, OPENSEARCH_ENDPOINT, OPENSEARCH_INDEX env vars, ingestion.embedder output
