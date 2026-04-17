# PURPOSE: In-memory FAISS index that serves dense-only retrieval when OpenSearch is unavailable
# CALLED BY: retrieval.retriever (on OpenSearch connection failure)
# DEPENDS ON: faiss-cpu, numpy, local .faiss index file path
