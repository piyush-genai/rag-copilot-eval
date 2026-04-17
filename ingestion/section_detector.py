# PURPOSE: Detects logical section boundaries (headings, numbered steps) in extracted PDF text
# CALLED BY: ingestion.chunker
# DEPENDS ON: re (stdlib), ingestion.pdf_extractor output

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

from ingestion.pdf_extractor import PageObject

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Known section names — exact match (case-insensitive)
# why: exact-match known names are the highest-confidence signal. They cover
# the standard runbook vocabulary and avoid false positives from short lines
# that happen to look like headings (e.g. "No issues found").
# ---------------------------------------------------------------------------
KNOWN_SECTION_NAMES: set[str] = {
    "overview", "prerequisites", "on-call", "shifts", "alerts", "incidents",
    "communication", "troubleshooting", "resolution", "verification", "rollback",
    "escalation", "notes", "schema", "modification", "contributing", "summary",
    "definition", "requirements", "installation", "configuration", "usage",
    "examples", "checklist", "steps", "procedure", "monitoring", "deployment",
    "access", "security", "learning", "deploy", "restore",
}

# Signal 2: prefixes that indicate a line is code/shell, not a heading
_CODE_PREFIXES = ("$", "#!", "user@", "apt", "make", "git ", "curl", "wget", "•", "-", "*")

# Signal 3: numbered section header — "1. Overview" or "2.1 Prerequisites"
_NUMBERED_HEADING_RE = re.compile(r'^\d+\.(\d+\.)?\s+[A-Z][a-z]')

# Signal 4: ALL CAPS short line — "PREREQUISITES", "ROLLBACK PROCEDURE"
_ALL_CAPS_RE = re.compile(r'^[A-Z][A-Z\s\-]{3,40}$')

# URL indicators — lines containing these are not headings
_URL_INDICATORS = ("http://", "https://", ".com", ".net", ".org", ".io")


@dataclass
class SectionObject:
    section_name: str   # detected heading text, or "Full Document" for fallback
    page_start: int     # 1-indexed page where section begins
    page_end: int       # 1-indexed page where section ends (inclusive)
    text: str           # full combined text of this section across all its pages


def _is_heading(line: str) -> bool:
    """
    Return True if a line matches any heading detection signal (priority order).

    Signals applied in order — first match wins:
      1. Known section name exact match
      2. Short line heuristic (catches corpus-specific headings)
      3. Numbered section header regex
      4. ALL CAPS short line regex
    """
    stripped = line.strip()
    if not stripped or len(stripped) < 2:
        return False

    lower = stripped.lower()

    # Signal 1: known section name exact match
    if lower in KNOWN_SECTION_NAMES:
        return True

    # Signal 3: numbered heading — check before short-line to avoid false positives
    if _NUMBERED_HEADING_RE.match(stripped):
        return True

    # Signal 4: ALL CAPS
    if _ALL_CAPS_RE.match(stripped):
        return True

    # Signal 2: short line heuristic
    words = stripped.split()
    if len(words) >= 10:
        return False
    if stripped[-1] in ".?,":
        return False
    if stripped.startswith(_CODE_PREFIXES):
        return False
    if any(indicator in stripped for indicator in _URL_INDICATORS):
        return False
    if re.match(r'^[\d\W]+$', stripped):
        return False

    return True


def detect_sections(pages: list[PageObject]) -> list[SectionObject]:
    """
    Detect logical section boundaries across a list of pages.

    Args:
        pages: Output of pdf_extractor.extract_pdf() — one PageObject per page.

    Returns:
        List of SectionObject. Falls back to a single "Full Document" section
        if fewer than 2 sections are detected.

    Raises:
        RuntimeError: If section detection fails unexpectedly.
    """
    try:
        # Collect (page_num, heading_text, line_index) for every detected heading
        heading_hits: list[tuple[int, str]] = []  # (page_num, heading_text)

        for page in pages:
            if not page.has_text:
                continue
            for line in page.text.splitlines():
                if _is_heading(line):
                    heading_hits.append((page.page_num, line.strip()))
                    break  # only take the first heading per page to avoid over-splitting
                    # why: taking only the first heading per page prevents a page with
                    # multiple short lines (e.g. a table of contents) from generating
                    # dozens of spurious single-line sections.

        # Build SectionObjects from heading hits
        sections: list[SectionObject] = []
        all_pages = [p for p in pages if p.has_text]

        if len(heading_hits) < 2:
            # Fallback: treat entire document as one section
            # why: returning "Full Document" loses section-level retrieval precision.
            # A query for "troubleshooting" will retrieve the entire document instead
            # of just the Troubleshooting section, diluting context_precision.
            # This is acceptable only when the document has no detectable structure.
            source_name = f"page_count={len(pages)}"
            logger.warning(
                json.dumps({
                    "event": "section_detection_fallback",
                    "source_runbook": source_name,
                    "page_count": len(pages),
                    "reason": "fewer_than_2_sections"
                })
            )
            full_text = "\n".join(p.text for p in all_pages)
            first_page = pages[0].page_num if pages else 1
            last_page = pages[-1].page_num if pages else 1
            return [SectionObject(
                section_name="Full Document",
                page_start=first_page,
                page_end=last_page,
                text=full_text
            )]

        # Map page_num → page text for fast lookup
        page_text_map: dict[int, str] = {p.page_num: p.text for p in pages if p.has_text}
        all_page_nums = sorted(page_text_map.keys())

        for i, (start_page, heading) in enumerate(heading_hits):
            # Section ends just before the next heading's page, or at the last page
            if i + 1 < len(heading_hits):
                end_page = heading_hits[i + 1][0] - 1
            else:
                end_page = all_page_nums[-1]

            # Clamp end_page to at least start_page
            end_page = max(end_page, start_page)

            # Collect text from all pages in this section's range
            section_pages = [
                page_text_map[pn]
                for pn in all_page_nums
                if start_page <= pn <= end_page
            ]
            section_text = "\n".join(section_pages)

            sections.append(SectionObject(
                section_name=heading,
                page_start=start_page,
                page_end=end_page,
                text=section_text
            ))

        return sections

    except Exception as e:
        raise RuntimeError(f"section_detector failed: {e}") from e
