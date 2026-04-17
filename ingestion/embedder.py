# PURPOSE: Calls Bedrock Titan Embeddings V2 to produce float32[1536] vectors for each chunk
# CALLED BY: ingestion.lambda_handler
# DEPENDS ON: boto3 (bedrock-runtime), AWS_REGION, BEDROCK_EMBEDDING_MODEL_ID env vars
