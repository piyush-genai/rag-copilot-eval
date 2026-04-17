# Corpus Findings — Pre-Implementation PDF Exploration

**Corpus:** ~200 GitLab-style technical operations runbooks (Markdown converted to PDF)  
**PDFs Explored:** AGENTS.md.pdf, README.pdf, services_README.pdf  
**Purpose:** Understand the actual structure of the data before writing ingestion code.

---

## Finding 1 — Heading Styles Are Inconsistent Across Documents

No single regex pattern covers all heading styles in this corpus. Three distinct styles were observed:

| Document | Heading Style | Examples |
|---|---|---|
| AGENTS.md.pdf | Title-case standalone lines | `Overview`, `CI/CD Structure`, `Common Commands` |
| README.pdf | Title-case with sub-sections | `On-Call`, `Shifts`, `Alerts`, `Incidents` |
| services_README.pdf | Sentence-case phrases | `Definition of a Service`, `Core Characteristics`, `Schema` |

**Design implication:** Section detection requires a ranked multi-signal strategy, not a single pattern. Signals are applied in priority order — highest-confidence first — so that a known section name like `Overview` is never misclassified by a weaker heuristic.

---

## Finding 2 — Merged Words Are a Real Encoding Problem

pdfplumber collapses spaces in certain PDF encodings produced by Markdown-to-PDF converters. Observed in README.pdf:

**Page 2:**
```
gotothefleetoverviewdashboardandcheckthenumberofActiveAlerts
```

**Page 3:**
```
Ifyoudoendupneedingtopostandupdateaboutanincident
```

This occurs most frequently in bullet points and hyperlink text. Body prose is usually unaffected.

**Design implication:** A word-boundary repair pass runs before section detection. Detection signal: token length > 25 characters with no hyphens, underscores, or digits. Auto-correction is intentionally not attempted — false positives on technical identifiers (e.g. `payment-api-v2-restart`) are worse than flagging for review. Merged words are logged with page number for manual inspection.

---

## Finding 3 — Tables Are Present and Will Be Garbled by Default Text Extraction

From AGENTS.md.pdf Page 2, a 4-column CI/CD job table was rendered by `extract_text()` as:

```
ensure-generated-contetnets-tup-tgoit-ladba.tceom Verifies make generate
```

That is one row of a structured table collapsed into a single garbled line. The actual table structure is only recoverable via `page.extract_tables()`.

**Design implication:** The `PageObject` dataclass stores `text` (body prose, table regions excluded) and `tables` (raw structured data from `extract_tables()`) as separate fields. Table content is excluded from body text by filtering words whose bounding boxes overlap with detected table regions. Tables in runbooks are reference material (error code tables, flag reference tables) and are stored as atomic units — never split mid-row.

---

## Finding 4 — No Explicit Step Numbers in This Corpus

None of the three PDFs use `Step 1:`, `1.`, or `1)` patterns for procedural steps. Steps are implicit — narrative sentences followed by bash command blocks:

```
[Short sentence introducing a task]
[Bash command block]
[Optional verification sentence]
```

**Design implication:** Step-number detection cannot be used as a chunk boundary signal for this corpus. Chunk boundaries are determined by section boundaries (hard) and token count (soft). Numbered heading patterns (`1. Overview`, `2.1 Prerequisites`) are still supported in the section detector for robustness across other corpora.

---

## Finding 5 — Bash Command Blocks Are a Critical Structural Element

Every operational runbook in this corpus contains bash command blocks. These must never be split mid-command. Observed pattern:

```
user@aptly:~$ sudo su - aptly
aptly@aptly:~$ aptly publish switch xenial gitlab-utils gitlab-utils-stable-$(date +"%Y%m%d")
```

A command block begins with `user@host:~$` or a bare `$` prompt and ends when the next prose line begins.

**Design implication:** The chunker's split-point logic must detect command block boundaries and back up to the nearest safe split point (end of the preceding prose line) rather than splitting mid-command. A chunk that says "run this command" without the command is not a retrievable answer.

---

## Summary — Parameters Derived From These Findings

| Parameter | Value | Reasoning |
|---|---|---|
| `CHUNK_SIZE_TOKENS` | 400 | Fits ~1-2 complete procedural units. A bash block + surrounding context runs 150-250 tokens. |
| `OVERLAP_TOKENS` | 30 | Runbook steps have low cross-dependency. 30 tokens carries the end of one step into the next chunk. |
| `MIN_CHUNK_TOKENS` | 100 | Below this, a chunk cannot stand alone as a retrievable answer. Trailing micro-chunks are merged backward. |
| `MERGED_WORD_MIN_LEN` | 25 | Threshold for flagging likely merged words. Technical identifiers rarely exceed this without hyphens or digits. |

---

## What Was Not Observed (But Handled for Robustness)

- ALL CAPS headings (`PREREQUISITES`, `ROLLBACK PROCEDURE`) — not present in this corpus but common in enterprise runbooks. Signal 4 in section detector handles them.
- Numbered section headers (`1. Overview`, `2.1 Prerequisites`) — not present in this corpus but present in other GitLab-style docs. Signal 3 handles them.
- Multi-column PDF layouts — not observed but `extract_text()` handles them via word-level bbox reconstruction.
