# PURPOSE: Handles POST /query — validates input, calls retriever, assembles prompt, invokes Claude
# CALLED BY: gateway.main (FastAPI route)
# DEPENDS ON: retrieval.retriever, gateway.sse_streamer, boto3 (bedrock-runtime), BEDROCK_MODEL_ID env var
