# PURPOSE: Re-scores fused top-k chunks against the query using a cross-encoder model, returns top-5
# CALLED BY: retrieval.retriever
# DEPENDS ON: sentence-transformers (CrossEncoder), HUGGINGFACE_TOKEN env var
