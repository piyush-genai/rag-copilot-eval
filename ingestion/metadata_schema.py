# PURPOSE: Defines the Pydantic model for chunk metadata — chunk_id, source_runbook, section_name, etc.
# CALLED BY: ingestion.chunker, ingestion.index_writer, retrieval.retriever
# DEPENDS ON: pydantic

from __future__ import annotations

import hashlib
import os
import re
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from ingestion.section_detector import SectionObject

# Regex to strip version numbers and environment suffixes from filenames
# e.g. "payment-api-v2-prod.pdf" → "payment-api"
_FILENAME_CLEANUP_RE = re.compile(
    r'[-_]?(v\d+[\d.]*|prod|staging|dev|uat|qa|test|latest)[-_]?',
    re.IGNORECASE
)

VALID_SEVERITY_LEVELS = {"P1", "P2", "P3", "P4", "unknown"}


class ChunkMetadata(BaseModel):
    chunk_id: str           # SHA-256(source_runbook + section_name + chunk_index)[:16]
    source_runbook: str     # S3 object key, e.g. "runbooks/aptly.pdf"
    section_name: str       # From SectionObject. "Full Document" if fallback.
    page_num: int           # Page where this chunk's text begins
    service_name: str       # Extracted from filename or first paragraph. "" if unknown.
    team_owner: str         # Extracted from filename or header. "" if unknown.
    severity_level: str     # "P1" | "P2" | "P3" | "P4" | "unknown"
    last_updated: str       # ISO 8601. S3 LastModified of source PDF. "" if unavailable.
    chunk_text: str         # The actual chunk content
    embedding: list[float]  # Populated by embedder.py. Empty list [] at schema creation.

    @classmethod
    def from_section(
        cls,
        section: "SectionObject",
        chunk_text: str,
        chunk_index: int,
        source_pdf_path: str,
    ) -> "ChunkMetadata":
        """
        Construct a ChunkMetadata from a SectionObject and a chunk of its text.

        Args:
            section:        The SectionObject this chunk belongs to.
            chunk_text:     The text content of this specific chunk.
            chunk_index:    0-based index of this chunk within its section.
            source_pdf_path: Local path or S3 key of the source PDF.
                             Used to derive service_name and source_runbook.

        Returns:
            ChunkMetadata with embedding=[] and severity_level="unknown".
        """
        # Derive the S3-style source key from the path
        # e.g. "/tmp/runbooks/aptly.pdf" → "runbooks/aptly.pdf"
        source_runbook = _normalise_source_key(source_pdf_path)

        # Derive service_name from the filename stem
        service_name = _extract_service_name(source_pdf_path)

        # Generate deterministic chunk_id
        chunk_id = _make_chunk_id(source_runbook, section.section_name, chunk_index)

        return cls(
            chunk_id=chunk_id,
            source_runbook=source_runbook,
            section_name=section.section_name,
            page_num=section.page_start,
            service_name=service_name,
            team_owner="",          # enriched externally — not derivable from PDF alone
            severity_level="unknown",
            # why: defaulting to "unknown" rather than "P3" prevents silently mislabelling
            # P1 emergency runbooks as P3. A P1 runbook labelled P3 would be deprioritized
            # in severity-filtered queries during a real incident — exactly when it matters most.
            last_updated="",        # populated by lambda_handler from S3 LastModified
            chunk_text=chunk_text,
            embedding=[],           # populated by embedder.py after schema creation
        )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _normalise_source_key(path: str) -> str:
    """
    Convert a local path or S3 key to a normalised S3-style key.
    Strips leading slashes and common temp prefixes.
    """
    # Remove leading /tmp/ or similar temp prefixes
    normalised = re.sub(r'^/tmp/', '', path)
    normalised = normalised.lstrip('/')
    return normalised


def _extract_service_name(path: str) -> str:
    """
    Derive a clean service name from a PDF filename.

    Examples:
        "aptly.pdf"              → "aptly"
        "payment-api-v2-prod.pdf" → "payment-api"
        "runbooks/db-backup.pdf"  → "db-backup"
    """
    filename = os.path.basename(path)
    stem = os.path.splitext(filename)[0]  # remove .pdf

    # Strip version numbers and environment suffixes
    cleaned = _FILENAME_CLEANUP_RE.sub('-', stem)

    # Remove trailing/leading hyphens or underscores left by substitution
    cleaned = cleaned.strip('-_')

    return cleaned.lower() if cleaned else ""


def _make_chunk_id(source_runbook: str, section_name: str, chunk_index: int) -> str:
    """
    Generate a deterministic 16-character chunk ID via SHA-256.

    Deterministic so re-ingestion of the same document produces the same IDs,
    enabling upsert (not duplicate insert) in OpenSearch.
    """
    raw = f"{source_runbook}::{section_name}::{chunk_index}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]
