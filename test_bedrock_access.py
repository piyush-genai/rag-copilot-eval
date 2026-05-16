# PURPOSE: One-time test to verify Bedrock Titan Embeddings V2 access
# Run: python3 test_bedrock_access.py
# Delete this file after confirming access works.

import json
import boto3

print("Testing Bedrock Titan Embeddings V2 access...")

try:
    client = boto3.client("bedrock-runtime", region_name="us-east-1")

    response = client.invoke_model(
        modelId="amazon.titan-embed-text-v2:0",
        contentType="application/json",
        accept="application/json",
        body=json.dumps({"inputText": "restart the payment service"})
    )

    result = json.loads(response["body"].read())
    embedding = result["embedding"]

    print(f"SUCCESS — Embedding dimension: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")
    print("Bedrock Titan V2 is accessible. Ready for Day 5.")

except Exception as e:
    print(f"FAILED — {type(e).__name__}: {e}")
    print()
    if "AccessDeniedException" in str(type(e)):
        print("Fix: Go to AWS Console → Bedrock → Model access → Request access for Titan Embeddings V2")
    elif "Could not connect" in str(e) or "credentials" in str(e).lower():
        print("Fix: Check AWS credentials — run: aws sts get-caller-identity")
