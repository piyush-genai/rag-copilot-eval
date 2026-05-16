# PURPOSE: Generates embeddings for text chunks using either Bedrock or local model
# CALLED BY: ingestion.lambda_handler, scripts/build_index.py
# DEPENDS ON: boto3 (bedrock-runtime) OR sentence-transformers (local)

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ─── EMBEDDING STRATEGY TOGGLE ────────────────────────────────────────────────

# Set to False to use local embeddings (no AWS, no cost, no quota issues).
# Set to True to use Bedrock Titan Embeddings V2 (requires quota approval).
# Why toggle: Allows development to continue while waiting for AWS quota increase.
# When Bedrock quota is approved, flip this to True and rebuild the index.
USE_BEDROCK = os.getenv("USE_BEDROCK", "false").lower() == "true"


# ─── BEDROCK CONFIGURATION ────────────────────────────────────────────────────

# Bedrock model ID for Titan Embeddings V2.
# Why Titan V2: trained on technical and enterprise text, better representation
# of system names, commands, and procedures than general-purpose models.
# 1536-dim vectors — higher dimensional = more nuanced semantic representation.
DEFAULT_MODEL_ID = "amazon.titan-embed-text-v2:0"

# Maximum chunks per embedding API call.
# Why 10: Bedrock Titan V2 supports up to 25, but reduced to avoid throttling
# on new accounts with lower limits. Increase to 25 once quota is stable.
BEDROCK_BATCH_SIZE = 10

# Retry configuration for throttling errors.
# Why exponential backoff: Bedrock rate limits are per-account. During bulk
# ingestion (200 runbooks × 10 chunks each = 2000 embedding calls), throttling
# is expected. Exponential backoff spreads retries over time instead of hammering
# the API immediately.
MAX_RETRIES = 5
INITIAL_BACKOFF_SECONDS = 2.0  # starts at 2s, then 4s, 8s, 16s, 32s


# ─── LOCAL MODEL CONFIGURATION ────────────────────────────────────────────────

# Local embedding model from sentence-transformers.
# Why all-MiniLM-L6-v2: Small (80MB), fast on CPU, 384-dim vectors, good quality
# for semantic search. Trained on 1B+ sentence pairs.
# Trade-off: 384-dim vs Bedrock's 1536-dim = less nuanced but sufficient for dev.
LOCAL_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Batch size for local embedding.
# Why 32: sentence-transformers processes batches efficiently on CPU. Larger
# batches = better GPU/CPU utilization. No API rate limits to worry about.
LOCAL_BATCH_SIZE = 32

# Lazy-loaded model instance (initialized on first use).
# Why lazy loading: Avoids loading the 80MB model if USE_BEDROCK=True.
_local_model: Optional[Any] = None


# ─── PUBLIC FUNCTION ──────────────────────────────────────────────────────────

def embed_chunks(chunks: list[dict]) -> list[dict]:
    """
    Embed a list of chunk dicts using either Bedrock or local model.

    Each chunk dict must have a "text" key. The embedding is added in-place
    as chunk["embedding"] = [float, float, ...].

    Why in-place modification: avoids copying the entire chunk dict. The chunk
    already has all its metadata — we're just adding the embedding field.

    Args:
        chunks: List of chunk dicts from chunker.py. Each must have "text" key.

    Returns:
        The same list of chunks, now with chunk["embedding"] populated.

    Raises:
        RuntimeError: If embedding fails after all retries (Bedrock only).
    """
    if not chunks:
        # Edge case: empty list. Nothing to embed.
        # Why handle explicitly: avoids unnecessary API calls or model loading.
        return chunks

    if USE_BEDROCK:
        logger.info("Using Bedrock Titan Embeddings V2 (1536-dim)")
        return _embed_with_bedrock(chunks)
    else:
        logger.info(f"Using local model {LOCAL_MODEL_NAME} (384-dim)")
        return _embed_with_local_model(chunks)


# ─── BEDROCK IMPLEMENTATION ───────────────────────────────────────────────────

def _embed_with_bedrock(chunks: list[dict]) -> list[dict]:
    """
    Embed chunks using Bedrock Titan Embeddings V2.

    Why separate function: keeps Bedrock-specific logic isolated. If Bedrock
    imports fail (e.g., boto3 not installed), local embeddings still work.
    """
    import boto3
    from botocore.exceptions import ClientError

    # Get AWS region and model ID from environment variables.
    # Why environment variables: Lambda and local dev use different AWS configs.
    region = os.getenv("AWS_REGION", "us-east-1")
    model_id = os.getenv("BEDROCK_EMBEDDING_MODEL_ID", DEFAULT_MODEL_ID)

    # Create the Bedrock runtime client.
    # Why bedrock-runtime (not bedrock): bedrock-runtime is the service for
    # invoking models. "bedrock" is the control plane for managing models.
    client = boto3.client("bedrock-runtime", region_name=region)

    # Process chunks in batches of BEDROCK_BATCH_SIZE.
    # Why batching: reduces API call count. 2000 chunks = 200 batch calls instead
    # of 2000 individual calls. Faster and cheaper.
    for batch_start in range(0, len(chunks), BEDROCK_BATCH_SIZE):
        batch_end = min(batch_start + BEDROCK_BATCH_SIZE, len(chunks))
        batch = chunks[batch_start:batch_end]

        # Extract just the text from each chunk in this batch.
        texts = [chunk["text"] for chunk in batch]

        # Call Bedrock with retry logic.
        embeddings = _bedrock_api_call_with_retry(client, model_id, texts)

        # Assign embeddings back to the chunk dicts.
        # Why zip: pairs each chunk with its corresponding embedding in order.
        for chunk, embedding in zip(batch, embeddings):
            chunk["embedding"] = embedding

        logger.info(
            "Embedded batch %d-%d (%d chunks) via Bedrock",
            batch_start, batch_end - 1, len(batch)
        )

        # Add a small delay between batches to avoid rate limiting.
        # Why 0.5s: Bedrock has per-second rate limits. Adding a gap between
        # successful calls reduces the chance of hitting the limit.
        if batch_end < len(chunks):  # Don't sleep after the last batch
            time.sleep(0.5)

    return chunks


def _bedrock_api_call_with_retry(
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
    from botocore.exceptions import ClientError

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
            response_body = json.loads(response["body"].read())

            # Extract embeddings from the response.
            # Titan V2 response structure: {"embedding": [float, ...]} for single input
            # or {"embeddings": [[...], [...]]} for batch input.
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
                    backoff *= 2  # exponential: 2s → 4s → 8s → 16s → 32s
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
    raise RuntimeError("_bedrock_api_call_with_retry: unreachable code path")


# ─── LOCAL MODEL IMPLEMENTATION ───────────────────────────────────────────────

def _embed_with_local_model(chunks: list[dict]) -> list[dict]:
    """
    Embed chunks using a local sentence-transformers model.

    Why separate function: keeps local model logic isolated. If sentence-transformers
    isn't installed, Bedrock path still works.
    """
    global _local_model

    # Lazy-load the model on first use.
    # Why lazy loading: model loading takes ~2 seconds and uses 80MB RAM.
    # Only pay this cost if actually using local embeddings.
    if _local_model is None:
        logger.info(f"Loading local model {LOCAL_MODEL_NAME}...")
        from sentence_transformers import SentenceTransformer
        _local_model = SentenceTransformer(LOCAL_MODEL_NAME)
        logger.info("Local model loaded")

    # Process chunks in batches of LOCAL_BATCH_SIZE.
    # Why batching: sentence-transformers is optimized for batch processing.
    # Batching improves CPU/GPU utilization.
    for batch_start in range(0, len(chunks), LOCAL_BATCH_SIZE):
        batch_end = min(batch_start + LOCAL_BATCH_SIZE, len(chunks))
        batch = chunks[batch_start:batch_end]

        # Extract just the text from each chunk in this batch.
        texts = [chunk["text"] for chunk in batch]

        # Generate embeddings.
        # Why encode: sentence-transformers' main API. Returns numpy array of shape
        # (batch_size, embedding_dim). convert_to_numpy=True ensures numpy output.
        embeddings = _local_model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False  # Why False: avoid cluttering logs during bulk processing
        )

        # Assign embeddings back to the chunk dicts.
        # Why .tolist(): converts numpy array to Python list for JSON serialization.
        for chunk, embedding in zip(batch, embeddings):
            chunk["embedding"] = embedding.tolist()

        logger.info(
            "Embedded batch %d-%d (%d chunks) via local model",
            batch_start, batch_end - 1, len(batch)
        )

    return chunks
