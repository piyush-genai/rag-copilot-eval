# PURPOSE: Wraps Bedrock InvokeModelWithResponseStream output as Server-Sent Events for the client
# CALLED BY: gateway.query_handler
# DEPENDS ON: fastapi (StreamingResponse), boto3 bedrock-runtime streaming response
