# PURPOSE: Split a single runbook section into overlapping token-bounded chunks
# CALLED BY: ingestion/lambda_handler.py (once per section, per document)
# DEPENDS ON: tiktoken, ingestion/metadata_schema.py

import tiktoken  # Library that counts tokens the same way embedding models do
import hashlib   # Built-in Python library for generating hash IDs


# ─── PARAMETERS ───────────────────────────────────────────────────────────────
# These are module-level constants. UPPER_CASE means "don't change this
# casually — it affects every chunk in the system."

CHUNK_SIZE_TOKENS = 400
# Why 400: Fits ~1-2 complete procedural units. Focused enough for retrieval
# precision. Large enough to be a standalone answer.
# If you set this to 256: chunks are too small, steps get fragmented.
# If you set this to 700: chunks are too large, retrieval precision drops.

OVERLAP_TOKENS = 30
# Why 30: Runbook steps have low cross-dependency. 30 tokens (~20 words)
# carries the end of the previous step into the next chunk — enough to
# preserve "run the command from step 2" references.
# For financial prose (india-equity-rag) you'd use 50 — more narrative dependency.

MIN_CHUNK_TOKENS = 100
# Why 100: Below this a chunk can't stand alone as an answer.
# "See Section 4 for details" = ~8 tokens. Useless to embed and index alone.
# These micro-chunks get merged into the previous chunk instead.

ENCODING = "cl100k_base"
# Why cl100k_base: This is the tokenisation scheme used by Titan Embeddings V2.
# Using it here means our token counts match what the embedding model processes.

# Bash prompt patterns — lines starting with these are inside command blocks.
# Why a tuple: Python's str.startswith() accepts a tuple and checks all of them.
BASH_LINE_PREFIXES = (
    "$", "user@", "root@", "aptly@", "ubuntu@",  # shell prompts
    "sudo ", "apt ", "apt-get ", "make ", "git ",  # common commands
    "curl ", "wget ", "systemctl ", "kubectl ",
    "aws ", "docker ", "python ", "python3 ",
)


# ─── PUBLIC FUNCTION ──────────────────────────────────────────────────────────

def chunk_section(section_text: str, metadata: dict) -> list[dict]:
    """
    Split one runbook section into overlapping chunks.

    Why section-level (not document-level): Each section answers a different
    class of question. Prerequisites answers "what do I need?" Steps answers
    "how do I do it?" Chunking across boundaries dilutes both.

    Args:
        section_text: Full text of one detected section (string).
        metadata: Dict with source_runbook, section_name, service_name,
                  team_owner, severity_level, page_num. Copied into every chunk.

    Returns:
        List of dicts. Each dict is one chunk: text + chunk_index + chunk_id
        + all metadata fields spread in.
    """

    # Step 1: Get the encoder object. We'll use it to convert text → tokens
    # and tokens → text.
    enc = tiktoken.get_encoding(ENCODING)

    # Step 2: Convert the entire section text into a list of integer tokens.
    # Example: "restart the service" → [15678, 279, 2532]
    # Each integer represents one token (roughly one word or word-piece).
    tokens = enc.encode(section_text)

    # Step 3: Edge case — section fits in a single chunk. Return immediately.
    # Why not skip this: if we let it fall into the while loop below, it works
    # but is harder to reason about. Explicit is better.
    if len(tokens) <= CHUNK_SIZE_TOKENS:
        chunk_text = enc.decode(tokens)  # convert tokens back to string
        return [_build_chunk(chunk_text, 0, metadata)]

    # Step 4: Sliding window loop.
    chunks = []   # This list collects all chunks we produce.
    start = 0     # start is the index of the first token in the current chunk.

    while start < len(tokens):

        # Calculate where this chunk wants to end (before safe-split adjustment).
        raw_end = min(start + CHUNK_SIZE_TOKENS, len(tokens))

        # Adjust end backward if it lands inside a bash command block.
        # Why: splitting mid-command gives the engineer a useless fragment.
        end = _find_safe_split_point(tokens, raw_end, enc)

        # Slice the tokens for this chunk.
        chunk_tokens = tokens[start:end]

        # Handle trailing micro-chunk: if this is a tiny leftover piece,
        # merge it into the previous chunk instead of creating a stub.
        if len(chunk_tokens) < MIN_CHUNK_TOKENS and chunks:
            # Append the tiny text to the last chunk's text field.
            chunks[-1]["text"] += " " + enc.decode(chunk_tokens)
            # Recalculate chunk_id because the text changed.
            # Why: chunk_id is a hash of the text position — it must stay consistent.
            chunks[-1]["chunk_id"] = _make_chunk_id(
                metadata.get("source_runbook", ""),
                metadata.get("section_name", ""),
                chunks[-1]["chunk_index"]
            )
            break  # No more chunks to produce — exit the loop.

        # Normal path: build a proper chunk and add to list.
        chunk_text = enc.decode(chunk_tokens)
        chunks.append(_build_chunk(chunk_text, len(chunks), metadata))

        # Advance the window. The next chunk starts at (end - OVERLAP_TOKENS)
        # so the last OVERLAP_TOKENS of this chunk become the first tokens
        # of the next chunk. This is the sliding window mechanism.
        next_start = end - OVERLAP_TOKENS

        # Safety guard: next_start must always be strictly greater than the
        # current start, otherwise the loop never terminates.
        # Why this can happen: _find_safe_split_point may back up so far on
        # repetitive or command-heavy text that end ≈ start + OVERLAP_TOKENS,
        # making next_start == start (no progress).
        if next_start <= start:
            next_start = start + max(1, CHUNK_SIZE_TOKENS - OVERLAP_TOKENS)

        start = next_start

    return chunks


# ─── PRIVATE HELPERS ──────────────────────────────────────────────────────────
# Functions starting with _ are private — only called inside this file.

def _find_safe_split_point(tokens: list, target_end: int, enc) -> int:
    """
    Back up from target_end to avoid splitting inside a bash command block.

    Why this exists: if token 400 falls mid-command, Chunk 2 starts with a
    command fragment the engineer can't execute. We back up to the nearest
    blank line or prose line before the command block.

    Args:
        tokens: The full token list for the section.
        target_end: Where we want to split (index into tokens list).
        enc: The tiktoken encoder (needed to decode tokens back to text).

    Returns:
        An adjusted end index (<= target_end). Never backs up more than
        MAX_BACKUP tokens — so we're always bounded.
    """
    MAX_BACKUP = 50  # Never back up more than 50 tokens looking for safe point.

    # Calculate the window we'll inspect: up to 50 tokens before target_end.
    # Why inspect this window: the unsafe content is in the lines just before
    # the split point, not far earlier.
    window_start = max(0, target_end - MAX_BACKUP)

    # Decode just that window back to readable text.
    window_text = enc.decode(tokens[window_start:target_end])

    # Split into individual lines.
    # rsplit("\n") splits on newlines. The result is a list of line strings.
    lines = window_text.split("\n")

    # Walk backward through the lines, looking for a safe boundary.
    # We track how many characters we backed up, then convert to tokens.
    chars_backed_up = 0

    for line in reversed(lines):
        # Check if this line is a bash command line.
        stripped = line.strip()  # remove leading/trailing whitespace

        is_bash_line = (
            stripped.startswith(BASH_LINE_PREFIXES) or  # starts with prompt/command
            stripped.endswith("\\") or                   # line continuation character
            (stripped.startswith("#") and len(stripped) < 60)  # short comment in script
        )

        if not is_bash_line and stripped == "":
            # Blank line — this is the ideal split point. Stop here.
            break

        if not is_bash_line and len(stripped) > 0:
            # Prose line — safe to split after this. Stop here.
            break

        # This line is part of a bash block. Back up past it.
        # +1 for the newline character that separated this line.
        chars_backed_up += len(line) + 1

    # If we didn't back up at all, return target_end unchanged.
    if chars_backed_up == 0:
        return target_end

    # Convert character backup to approximate token backup.
    # Why approximate: one token ≈ 4 characters in English text.
    # This is an approximation — precise enough for our purposes.
    token_backup = min(chars_backed_up // 4, MAX_BACKUP)

    # Return the adjusted end, but never go below window_start.
    adjusted_end = max(target_end - token_backup, window_start)
    return adjusted_end


def _build_chunk(text: str, index: int, metadata: dict) -> dict:
    """
    Assemble one chunk dictionary.

    Why a helper function: this same assembly logic is needed in two places
    (normal chunks and the single-chunk edge case). One function, not two
    copies of the same code.

    Args:
        text: The decoded string content of this chunk.
        index: Position of this chunk within its section (0-indexed).
        metadata: The metadata dict passed into chunk_section.

    Returns:
        A dict with text, chunk_index, chunk_id, and all metadata fields.
    """
    chunk_id = _make_chunk_id(
        metadata.get("source_runbook", ""),
        metadata.get("section_name", ""),
        index
    )
    # The ** operator "spreads" the metadata dict into this new dict.
    # It's equivalent to copying each key-value pair from metadata individually.
    return {
        "text": text,
        "chunk_index": index,
        "chunk_id": chunk_id,
        **metadata  # spreads source_runbook, section_name, service_name, etc.
    }


def _make_chunk_id(source_runbook: str, section_name: str, index: int) -> str:
    """
    Generate a deterministic 16-character chunk ID.

    Why deterministic (not random UUID): re-ingesting the same runbook must
    produce the same IDs. index_writer.py upserts by chunk_id — if IDs were
    random, every re-ingest would create duplicates instead of updating.

    Why SHA-256 truncated to 16 hex chars: collision-resistant at our scale
    (millions of chunks). Full 64-char SHA-256 wastes OpenSearch storage.
    16 chars = 64 bits of entropy — sufficient.

    Args:
        source_runbook: S3 key of the source PDF, e.g. "runbooks/aptly.pdf"
        section_name: Section heading, e.g. "Steps"
        index: Chunk position within the section.

    Returns:
        16-character hex string, e.g. "a3f7b2c1d4e5f609"
    """
    # Build the input string. :: separators prevent collisions between
    # ("run", "books/steps", 0) and ("runbooks", "/steps", 0).
    raw = f"{source_runbook}::{section_name}::{index}"

    # hashlib.sha256() computes the hash.
    # .encode() converts the string to bytes (SHA-256 needs bytes, not str).
    # .hexdigest() returns the hash as a hex string.
    # [:16] takes only the first 16 characters.
    return hashlib.sha256(raw.encode()).hexdigest()[:16]