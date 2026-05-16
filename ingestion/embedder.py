# PURPOSE: Calls Bedrock Titan Embeddings V2 to produce float32[1536] vectors for each chunk
# CALLED BY: ingestion.lambda_handler
# DEPENDS ON: boto3 (bedrock-runtime), AWS_REGION, BEDROCK_EMBEDDING_MODEL_ID env vars

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


# ─── CONFIGURATION ────────────────────────────────────────────────────────────

# Bedrock model ID for Titan Embeddings V2.
# Why Titan V2: trained on technical and enterprise text, better representation
# of system names, commands, and procedures than general-purpose models.
# 1536-dim vectors — higher dimensional = more nuanced semantic representation.
DEFAULT_MODEL_ID = "amazon.titan-embed-text-v2:0"

# Maximum chunks per embedding API call.
# Why 25: Bedrock Titan V2 batch limit. Exceeding this returns a validation error.
# Note: If you're getting throttled frequently, reduce this to 10 or 5 to spread
# the load over more API calls with longer gaps between them.
BATCH_SIZE = 10  # Reduced from 25 to avoid throttling on new accounts

# Retry configuration for throttling errors.
# Why exponential backoff: Bedrock rate limits are per-account. During bulk
# ingestion (200 runbooks × 10 chunks each = 2000 embedding calls), throttling
# is expected. Exponential backoff spreads retries over time instead of hammering
# the API immediately.
MAX_RETRIES = 5  # Increased from 3 for new accounts with lower limits
INITIAL_BACKOFF_SECONDS = 2.0  # Increased from 1.0 — starts at 2s, then 4s, 8s, 16s, 32s


# ─── PUBLIC FUNCTION ──────────────────────────────────────────────────────────

def embed_chunks(chunks: list[dict]) -> list[dict]:
    """
    Embed a list of chunk dicts by calling Bedrock Titan Embeddings V2.

    Each chunk dict must have a "text" key. The embedding is added in-place
    as chunk["embedding"] = [float, float, ...].

    Why in-place modification: avoids copying the entire chunk dict. The chunk
    already has all its metadata — we're just adding the embedding field.

    Args:
        chunks: List of chunk dicts from chunker.py. Each must have "text" key.

    Returns:
        The same list of chunks, now with chunk["embedding"] populated.

    Raises:
        RuntimeError: If Bedrock API call fails after all retries.
    """
    if not chunks:
        # Edge case: empty list. Nothing to embed.
        # Why handle explicitly: calling Bedrock with an empty batch returns
        # a validation error. Returning early is cleaner.
        return chunks

    # Get AWS region and model ID from environment variables.
    # Why environment variables: Lambda and local dev use different AWS configs.
    # Env vars let us switch without changing code.
    region = os.getenv("AWS_REGION", "us-east-1")
    model_id = os.getenv("BEDROCK_EMBEDDING_MODEL_ID", DEFAULT_MODEL_ID)

    # Create the Bedrock runtime client.
    # Why bedrock-runtime (not bedrock): bedrock-runtime is the service for
    # invoking models. "bedrock" is the control plane for managing models.
    client = boto3.client("bedrock-runtime", region_name=region)

    # Process chunks in batches of BATCH_SIZE.
    # Why batching: reduces API call count. 2000 chunks = 80 batch calls instead
    # of 2000 individual calls. Faster and cheaper.
    for batch_start in range(0, len(chunks), BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, len(chunks))
        batch = chunks[batch_start:batch_end]

        # Extract just the text from each chunk in this batch.
        texts = [chunk["text"] for chunk in batch]

        # Call Bedrock with retry logic.
        embeddings = _embed_batch_with_retry(client, model_id, texts)

        # Assign embeddings back to the chunk dicts.
        # Why zip: pairs each chunk with its corresponding embedding in order.
        for chunk, embedding in zip(batch, embeddings):
            chunk["embedding"] = embedding

        logger.info(
            "Embedded batch %d-%d (%d chunks)",
            batch_start, batch_end - 1, len(batch)
        )

        # Add a small delay between batches to avoid rate limiting.
        # Why 0.5s: Bedrock has per-second rate limits. Adding a gap between
        # successful calls reduces the chance of hitting the limit.
        # This adds ~40 seconds total for 2000 chunks (80 batches × 0.5s).
        if batch_end < len(chunks):  # Don't sleep after the last batch
            time.sleep(0.5)

    return chunks


# ─── PRIVATE HELPERS ──────────────────────────────────────────────────────────

def _embed_batch_with_retry(
    client: Any,
    model_id: str,
    texts: list[str]
) -> list[list[float]]:
    """
    Call Bedrock InvokeModel with exponential backoff on throttling errors.

    Why retry logic: Bedrock has per-account rate limits. During bulk ingestion,
    ThrottlingException is expected. Retrying with exponential backoff succeeds
    on the 2nd or 3rd attempt without failing the entire ingestion job.

    Args:
        client: boto3 bedrock-runtime client.
        model_id: Bedrock model ID, e.g. "amazon.titan-embed-text-v2:0".
        texts: List of strings to embed (max 25 per Bedrock batch limit).

    Returns:
        List of embeddings, one per input text. Each embedding is a list[float].

    Raises:
        RuntimeError: If all retries are exhausted.
    """
    backoff = INITIAL_BACKOFF_SECONDS

    for attempt in range(MAX_RETRIES):
        try:
            # Build the request body for Titan Embeddings V2.
            # Why inputText (not input_text): Bedrock API uses camelCase, not snake_case.
            # Why single string vs list: Titan V2 accepts either a single string or a list
            # of strings. Single string returns {"embedding": [...]}, list returns
            # {"embeddings": [[...], [...]]}.
            if len(texts) == 1:
                body = json.dumps({"inputText": texts[0]})
            else:
                body = json.dumps({"inputText": texts})

            # Call Bedrock InvokeModel.
            # Why InvokeModel (not InvokeModelWithResponseStream): embeddings are
            # returned as a single JSON response, not streamed tokens.
            response = client.invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=body
            )

            # Parse the response body.
            # Why json.loads: Bedrock returns a JSON string in response["body"].
            # We need to parse it to extract the embedding vectors.
            response_body = json.loads(response["body"].read())

            # Extract embeddings from the response.
            # Titan V2 response structure: {"embedding": [float, ...]} for single input
            # or {"embeddings": [[float, ...], ...]} for batch input.
            if "embedding" in response_body:
                # Single text input — wrap in a list for consistency.
                return [response_body["embedding"]]
            elif "embeddings" in response_body:
                # Batch input — return the list of embeddings directly.
                return response_body["embeddings"]
            else:
                raise RuntimeError(
                    f"Unexpected Bedrock response structure: {response_body.keys()}"
                )

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")

            # Check if this is a throttling error.
            # Why check error_code: only throttling errors should trigger retry.
            # Other errors (ValidationException, AccessDeniedException) should
            # fail immediately — retrying won't help.
            if error_code == "ThrottlingException":
                if attempt < MAX_RETRIES - 1:
                    logger.warning(
                        "Bedrock throttled on attempt %d/%d — retrying in %.1fs",
                        attempt + 1, MAX_RETRIES, backoff
                    )
                    time.sleep(backoff)
                    backoff *= 2  # exponential: 1s → 2s → 4s
                    continue  # retry
                else:
                    # All retries exhausted.
                    raise RuntimeError(
                        f"Bedrock throttled after {MAX_RETRIES} retries"
                    ) from e
            else:
                # Non-throttling error — fail immediately.
                raise RuntimeError(
                    f"Bedrock API error ({error_code}): {e}"
                ) from e

    # Should never reach here — loop always returns or raises.
    raise RuntimeError("embed_batch_with_retry: unreachable code path")
