# PURPOSE: Verify the full extraction pipeline on real PDFs before Day 3.
#          Run this manually — it is NOT a unit test. It prints human-readable
#          output so you can visually confirm the pipeline is working correctly.
# CALLED BY: You, manually: python explore_pdf.py
# DEPENDS ON: ingestion/pdf_extractor.py, ingestion/section_detector.py,
#             ingestion/chunker.py

import os
import sys

# Why this sys.path line: Python needs to find the ingestion/ package.
# When you run this script from the project root, Python's search path
# doesn't automatically include the project root. This line adds it.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tiktoken

from ingestion.pdf_extractor import extract_pdf
from ingestion.section_detector import detect_sections
from ingestion.chunker import chunk_section, ENCODING


# ─── CONFIGURATION ────────────────────────────────────────────────────────────

# PDFs to test. Pick a representative sample — one simple, one complex, one long.
# Why 5 PDFs: enough to catch edge cases (merged words, tables, no sections)
# without waiting 10 minutes for the full corpus.
TEST_PDFS = [
    "data/runbooks/pdf/runbooks_README.pdf",
    "data/runbooks/pdf/runbooks_AGENTS.pdf",
    "data/runbooks/pdf/runbooks_services_README.pdf",
    "data/runbooks/pdf/runbooks_docs_patroni_README.pdf",
    "data/runbooks/pdf/runbooks_docs_uncategorized_aptly.pdf",
]

# How many characters of chunk text to preview in the output.
# Why 200: enough to see if the chunk is coherent, not so much it floods the terminal.
CHUNK_PREVIEW_LEN = 200


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def count_tokens(text: str) -> int:
    """Count tokens in a string using the same encoding as the chunker."""
    enc = tiktoken.get_encoding(ENCODING)
    return len(enc.encode(text))


def print_separator(char: str = "─", width: int = 70) -> None:
    """Print a visual separator line. Makes the output easier to scan."""
    print(char * width)


def _make_metadata(pdf_path: str, section_name: str, page_num: int) -> dict:
    """
    Build a minimal metadata dict for chunk_section.

    Why needed: chunk_section requires a metadata dict. For exploration
    we don't have real service_name or team_owner — we use placeholders.
    The important fields are source_runbook and section_name.
    """
    filename = os.path.basename(pdf_path)
    return {
        "source_runbook": f"runbooks/pdf/{filename}",
        "section_name": section_name,
        "service_name": "",       # not extracted at this stage
        "team_owner": "",         # not extracted at this stage
        "severity_level": "unknown",
        "page_num": page_num,
    }


# ─── MAIN VERIFICATION FUNCTION ───────────────────────────────────────────────

def verify_pdf(pdf_path: str) -> dict:
    """
    Run the full extraction pipeline on one PDF and return a summary dict.

    Pipeline: pdf_extractor → section_detector → chunker
    This mirrors exactly what lambda_handler.py will do in production.

    Args:
        pdf_path: Path to the PDF file, relative to the project root.

    Returns:
        Summary dict with counts and any warnings found.
    """
    print_separator("═")
    print(f"FILE: {pdf_path}")
    print_separator("═")

    summary = {
        "pdf": pdf_path,
        "pages_total": 0,
        "pages_with_text": 0,
        "pages_empty": 0,
        "tables_found": 0,
        "merged_word_warnings": 0,
        "sections_found": 0,
        "fallback_triggered": False,
        "total_chunks": 0,
        "warnings": [],
    }

    # ── STAGE 1: PDF EXTRACTION ───────────────────────────────────────────────
    print("\n[STAGE 1] PDF Extraction")
    print_separator()

    # Why check file existence here: gives a clear error message instead of
    # a cryptic pdfplumber exception if the path is wrong.
    if not os.path.exists(pdf_path):
        msg = f"  ✗ FILE NOT FOUND: {pdf_path}"
        print(msg)
        summary["warnings"].append(msg)
        return summary

    pages = extract_pdf(pdf_path)
    summary["pages_total"] = len(pages)

    for page in pages:
        if page.has_text:
            summary["pages_with_text"] += 1
        else:
            summary["pages_empty"] += 1
            print(f"  ⚠ Page {page.page_num}: empty (cover page or image-only)")

        if page.tables:
            summary["tables_found"] += len(page.tables)

    print(f"  Pages total:      {summary['pages_total']}")
    print(f"  Pages with text:  {summary['pages_with_text']}")
    print(f"  Pages empty:      {summary['pages_empty']}")
    print(f"  Tables found:     {summary['tables_found']}")

    # Show a sample of the raw extracted text from page 1 so you can
    # visually check for merged words or garbled content.
    text_pages = [p for p in pages if p.has_text]
    if text_pages:
        sample_text = text_pages[0].text[:400]
        print(f"\n  Sample text (page {text_pages[0].page_num}, first 400 chars):")
        print("  " + "\n  ".join(sample_text.splitlines()[:8]))

    # ── STAGE 2: SECTION DETECTION ────────────────────────────────────────────
    print("\n[STAGE 2] Section Detection")
    print_separator()

    sections = detect_sections(pages)
    summary["sections_found"] = len(sections)

    # Check if fallback was triggered (only one section named "Full Document")
    if len(sections) == 1 and sections[0].section_name == "Full Document":
        summary["fallback_triggered"] = True
        print(f"  ⚠ FALLBACK TRIGGERED — no sections detected, using 'Full Document'")
        print(f"    This means section-level filtering won't work for this runbook.")
        print(f"    Check the raw text above — does it have detectable headings?")
    else:
        print(f"  Sections detected: {len(sections)}")

    # Print each section with its page range and character count.
    # Why character count: lets you spot sections that are suspiciously short
    # (might be a false positive heading detection) or very long (might need
    # more chunks than expected).
    for s in sections:
        token_count = count_tokens(s.text)
        print(f"  [{s.page_start:2d}-{s.page_end:2d}] {s.section_name:<35} "
              f"{len(s.text):5d} chars  {token_count:4d} tokens")

    # ── STAGE 3: CHUNKING ─────────────────────────────────────────────────────
    print("\n[STAGE 3] Chunking")
    print_separator()

    all_chunks = []

    for section in sections:
        metadata = _make_metadata(pdf_path, section.section_name, section.page_start)
        chunks = chunk_section(section.text, metadata)
        all_chunks.extend(chunks)

        # Flag sections that produced only 1 chunk — might be too short or
        # might be a sign the section text is mostly empty.
        status = "✓" if len(chunks) > 1 else "·"
        print(f"  {status} {section.section_name:<35} → {len(chunks):2d} chunk(s)")

    summary["total_chunks"] = len(all_chunks)

    print(f"\n  Total chunks produced: {summary['total_chunks']}")

    # Verify every chunk meets the minimum token threshold.
    # Why check here: if MIN_CHUNK_TOKENS logic is broken, we'd see tiny chunks
    # that would waste embedding API calls and pollute the vector store.
    short_chunks = [
        c for c in all_chunks
        if count_tokens(c["text"]) < 50  # 50 is a generous lower bound
    ]
    if short_chunks:
        print(f"\n  ⚠ {len(short_chunks)} chunk(s) under 50 tokens — check merge logic:")
        for c in short_chunks[:3]:  # show at most 3 examples
            print(f"    chunk_id={c['chunk_id']} | {count_tokens(c['text'])} tokens | "
                  f"'{c['text'][:60]}...'")

    # Show a sample chunk from the first section so you can visually verify
    # the text is coherent and not garbled.
    if all_chunks:
        sample = all_chunks[0]
        print(f"\n  Sample chunk (chunk_id={sample['chunk_id']}):")
        print(f"  Section: {sample['section_name']}")
        print(f"  Tokens:  {count_tokens(sample['text'])}")
        print(f"  Text preview:")
        preview = sample["text"][:CHUNK_PREVIEW_LEN].replace("\n", " ")
        print(f"    '{preview}...'")

    # ── SUMMARY ───────────────────────────────────────────────────────────────
    print("\n[SUMMARY]")
    print_separator()
    print(f"  ✓ Pages extracted:  {summary['pages_with_text']} / {summary['pages_total']}")
    print(f"  ✓ Sections found:   {summary['sections_found']}"
          + (" (FALLBACK)" if summary["fallback_triggered"] else ""))
    print(f"  ✓ Chunks produced:  {summary['total_chunks']}")

    if not summary["warnings"]:
        print("  ✓ No warnings")
    else:
        for w in summary["warnings"]:
            print(f"  ⚠ {w}")

    return summary


# ─── ENTRY POINT ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Why __name__ == "__main__": this block only runs when you execute this
    # file directly (python explore_pdf.py). It does NOT run when another
    # file imports from this module. Standard Python pattern.

    print("\n" + "═" * 70)
    print("  RAG PIPELINE VERIFICATION — Real PDF Extraction Test")
    print("  Run from project root: python explore_pdf.py")
    print("═" * 70 + "\n")

    all_summaries = []

    for pdf_path in TEST_PDFS:
        summary = verify_pdf(pdf_path)
        all_summaries.append(summary)
        print()  # blank line between PDFs

    # ── FINAL REPORT ──────────────────────────────────────────────────────────
    print_separator("═")
    print("FINAL REPORT — All PDFs")
    print_separator("═")
    print(f"{'PDF':<50} {'Pages':>6} {'Sections':>9} {'Chunks':>7} {'Fallback':>9}")
    print_separator()

    for s in all_summaries:
        name = os.path.basename(s["pdf"])[:48]
        fallback = "YES ⚠" if s["fallback_triggered"] else "no"
        print(f"{name:<50} {s['pages_with_text']:>6} {s['sections_found']:>9} "
              f"{s['total_chunks']:>7} {fallback:>9}")

    print_separator()

    # What to look for in the output:
    # ✓ Pages extracted should equal pages total (or close — cover pages are OK)
    # ✓ Sections found should be > 1 for most runbooks (fallback is a warning)
    # ✓ Chunks produced should be > 0 for every PDF
    # ✓ Sample text should be readable prose, not garbled characters
    # ✓ No chunks under 50 tokens (merge logic working)
    print("\nWhat to verify:")
    print("  1. Sample text is readable — no garbled characters or merged words")
    print("  2. Section names match the actual headings in the PDF")
    print("  3. Fallback count is low — most runbooks should have detectable sections")
    print("  4. Chunk counts are reasonable — not 1 per PDF, not 100+ per section")
    print("  5. No short chunk warnings\n")
