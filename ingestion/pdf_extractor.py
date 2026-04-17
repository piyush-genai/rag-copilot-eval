# PURPOSE: Extracts structured text and page numbers from raw PDF bytes using pdfplumber
# CALLED BY: ingestion.lambda_handler
# DEPENDS ON: pdfplumber, boto3 (S3 GetObject)

from __future__ import annotations

import io
import logging
import re
from dataclasses import dataclass, field
from typing import Union

import pdfplumber

# why: pdfplumber preserves layout structure (bounding boxes, line positions) which lets us
# detect headings by position and exclude table regions from body text.
# PyPDF2 flattens all content to a single stream with no spatial awareness.

logger = logging.getLogger(__name__)

MERGED_WORD_MIN_LEN = 25  # characters — threshold for flagging likely merged words


@dataclass
class PageObject:
    page_num: int           # 1-indexed
    text: str               # cleaned body text (table regions excluded)
    tables: list[list]      # raw table data from page.extract_tables()
    has_text: bool          # False if page returned empty text (cover page, image-only)


def _get_table_bboxes(page: pdfplumber.page.Page) -> list[tuple]:
    """Return bounding boxes of all tables on a page."""
    bboxes = []
    for table in page.find_tables():
        bboxes.append(table.bbox)  # (x0, top, x1, bottom)
    return bboxes


def _bbox_overlaps(word_bbox: tuple, table_bboxes: list[tuple]) -> bool:
    """Return True if a word's bbox overlaps with any table bbox."""
    wx0, wtop, wx1, wbottom = word_bbox
    for tx0, ttop, tx1, tbottom in table_bboxes:
        if wx0 < tx1 and wx1 > tx0 and wtop < tbottom and wbottom > ttop:
            return True
    return False


def _extract_text_excluding_tables(page: pdfplumber.page.Page) -> str:
    """
    Extract body text from a page, skipping words that fall inside table bounding boxes.

    # why: pdfplumber's extract_text() includes table cell content inline with body text,
    # producing garbled output like merged numbers and labels. By filtering words whose
    # bounding boxes overlap with detected table regions, we get clean prose only.
    """
    table_bboxes = _get_table_bboxes(page)

    if not table_bboxes:
        # No tables on this page — fast path, no filtering needed
        return page.extract_text() or ""

    words = page.extract_words()
    filtered_words = [
        w for w in words
        if not _bbox_overlaps((w["x0"], w["top"], w["x1"], w["bottom"]), table_bboxes)
    ]

    if not filtered_words:
        return ""

    # Reconstruct text from filtered words, preserving line breaks
    lines: dict[float, list[str]] = {}
    for w in filtered_words:
        line_key = round(w["top"], 1)
        lines.setdefault(line_key, []).append(w["text"])

    return "\n".join(" ".join(words) for _, words in sorted(lines.items()))


def _flag_merged_words(text: str, page_num: int) -> None:
    """
    Log any token that looks like a merged word (PDF encoding artifact).

    # why: auto-fixing merged words (e.g. splitting "gotothefleetoverviewdashboard")
    # requires a dictionary lookup and produces false positives on technical terms,
    # command names, and compound identifiers. Flagging for human review is safer.
    """
    for token in text.split():
        if (
            len(token) >= MERGED_WORD_MIN_LEN
            and not re.search(r'[-_\d]', token)
            and token.isalpha()
        ):
            logger.warning(
                "Possible merged word on page %d: %r (length=%d) — manual review needed",
                page_num, token, len(token)
            )


def extract_pdf(source: Union[str, bytes]) -> list[PageObject]:
    """
    Extract structured content from a PDF file or raw bytes.

    Args:
        source: Local file path (str) or raw PDF bytes (bytes).
                Bytes form is used when called from Lambda after S3 GetObject.

    Returns:
        List of PageObject, one per page, in page order.

    Raises:
        RuntimeError: If pdfplumber fails to open or parse the source.
    """
    try:
        if isinstance(source, bytes):
            pdf_file = io.BytesIO(source)
        else:
            pdf_file = source  # pdfplumber accepts a path string directly

        pages: list[PageObject] = []

        with pdfplumber.open(pdf_file) as pdf:
            for i, page in enumerate(pdf.pages):
                page_num = i + 1  # 1-indexed

                try:
                    # Extract tables first — stored separately from body text
                    # why: tables stored separately so downstream chunker and retriever
                    # can handle structured data differently from narrative prose.
                    # Inline table text garbles retrieval (merged numbers, broken labels).
                    raw_tables = page.extract_tables() or []

                    # Extract body text with table regions excluded
                    body_text = _extract_text_excluding_tables(page)

                    if not body_text or not body_text.strip():
                        logger.warning(
                            "Page %d returned empty text — likely a cover page or image-only page",
                            page_num
                        )
                        pages.append(PageObject(
                            page_num=page_num,
                            text="",
                            tables=raw_tables,
                            has_text=False
                        ))
                        continue

                    # Flag potential merged words from PDF encoding issues
                    _flag_merged_words(body_text, page_num)

                    pages.append(PageObject(
                        page_num=page_num,
                        text=body_text,
                        tables=raw_tables,
                        has_text=True
                    ))

                except Exception as page_err:
                    logger.error("Failed to process page %d: %s", page_num, page_err)
                    pages.append(PageObject(
                        page_num=page_num,
                        text="",
                        tables=[],
                        has_text=False
                    ))

        return pages

    except Exception as e:
        raise RuntimeError(f"pdf_extractor failed on {source!r}: {e}") from e
