# PURPOSE: Executes BM25 and KNN queries against OpenSearch Serverless and returns scored result lists
# CALLED BY: retrieval.retriever
# DEPENDS ON: opensearch-py, boto3 (AWS SigV4 auth), OPENSEARCH_ENDPOINT, OPENSEARCH_INDEX env vars
