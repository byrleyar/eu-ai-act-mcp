# EU AI Act Compliance MCP Server

## What This Is

An MCP server that helps users generate EU AI Act Article 53 GPAI compliance documentation from Hugging Face model cards. Claude fetches and enriches model card data, answers 50+ compliance questions, generates a downloadable Word document, and produces a companion PDF source citation report tracking the provenance and confidence of every answer. A batch CLI pipeline processes multiple models automatically, runs a Skeptical Auditor against each compliance form, and produces aggregate performance reports and a publication-ready analytical Markdown report. Deployed on Railway and usable from Claude Desktop or Claude.ai.

## Core Value

Every answer in the compliance document must be traceable back to its source — users need to trust and verify the generated compliance form.

## Current State

**Shipped v1.5** — 2026-03-03
**Stats:** 6,729 LOC Python, 117 tests passing.

**Key Accomplishments (v1.5):**
- ✓ **Analytical Report Generator**: `generate_report.py` CLI with 4-stage pipeline (Load → Join → Aggregate → Render) producing `batch_report.md` from batch `audit_results.json` files.
- ✓ **8 Statistical Tables**: Aggregate stats, per-model detail, by org type, by domain, section N/A rates, org-type breakdown with 15pp highlighting, hallucinated/incomplete question rankings.
- ✓ **Auto-Commentary**: `assemble_report()` derives commentary from actual computed values — names top sections, accuracy ranges, and problem question IDs.
- ✓ **9 CSV Exports**: `combined_field_audits.csv` (raw question-level data) + 8 table-specific CSVs per batch run.

## Requirements

### Validated

- ✓ PDF-based source citation report with confidence coloring — v1.1
- ✓ `generate_source_report` MCP tool with 24-hour file lifecycle — v1.1
- ✓ Pydantic citation data model with 4 confidence levels (DIRECT, INFERRED, NOT FOUND, HALLUCINATED) — v1.1
- ✓ HALLUCINATED confidence level with visual distinction (red) — v1.2
- ✓ Server-side citation coverage enforcement (mandatory citations for all 80+ questions) — v1.2
- ✓ Automatic end-to-end workflow (compliance doc + source report together) — v1.2
- ✓ Discovery engine: extract links from BibTeX, citation blocks, repo file lists — v1.3
- ✓ `fetch_external_document` MCP tool for on-demand paper retrieval with SSRF protection — v1.3
- ✓ Agentic Retrieval Workflow (Gap Analysis → Targeted Fetch loop) — v1.3
- ✓ BAT-01: Bulk processing of HuggingFace model IDs from CSV/list — v1.4
- ✓ BAT-02–04: Sequential orchestration with rate limiting, state isolation, fault tolerance — v1.4
- ✓ AUD-01–03: Skeptical Auditor LLM persona scoring 80 answers with hallucination detection — v1.4
- ✓ SCR-01–03: 1/1i/2/3/4 scoring rubric, persisted as structured JSON — v1.4
- ✓ REP-01–03: Hackathon-format Excel/CSV aggregate reports with executive summary — v1.4
- ✓ ANA-01: Publication-ready Markdown analytical report (`batch_report.md`) with 8 statistical tables — v1.5
- ✓ ANA-02: Auto-generated data-derived commentary naming real values from computed tables — v1.5
- ✓ ANA-03: Combined question-level CSV (`combined_field_audits.csv`) as raw analytical foundation — v1.5

### Active

- [ ] **Audit & Review Workflow**: Allow users to "approve" or "comment" on citations in a third step.
- [ ] **Regulatory Mapping**: Link each question ID to specific articles and measures in the EU AI Act.
- [ ] **Enhanced Document Linkage**: Embed source report links or QR codes directly in the DOCX compliance form.
- [ ] **Multi-batch Trend Analysis**: Compare analytical reports across batch runs to track compliance improvement over time.

### Out of Scope

- Parallel batch processing — sequential loop sufficient for current scale; parallelize when needed
- Human-in-the-loop review interface — future milestone
- Historical trend analysis across batch runs — future milestone
- Real-time dashboard for batch progress — CLI logs sufficient
- Mobile app / non-web clients — web-first approach
- Integration with non-Hugging Face model registries — HF-focused for now

## Context

Tech stack: Python 3.10+, FastMCP, python-docx, ReportLab 4.4.10, Pydantic v2, DejaVu Sans font family, Typer, Rich, openpyxl, pandas.
Deployed on Railway with persistent volume storage.

**Architecture:** FastMCP server with tools for model card fetching, requirements retrieval, and document generation (DOCX/PDF). `ComplianceService` encapsulates all core logic, shared by the MCP server and `batch_processor.py` CLI. Batch pipeline: batch_processor → audit_processor → report_generator → generate_report.

**Workflow:** User provides model ID → Claude fetches model card and link checklist → Claude performs gap analysis → Claude fetches specific missing docs → Claude generates compliance form and source report.

**Batch Workflow:** `batch_processor.py --input-csv models.csv` → per-model compliance artifacts → `audit_processor.py` → per-model `audit_results.json` → `report_generator.py` → `batch_report.xlsx` + `executive_summary.txt` → `generate_report.py` → `batch_report.md` (8 analytical tables + commentary) + 9 CSVs.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Agentic Retrieval | Shift from "fetch everything" to "fetch what is missing" to optimize context usage and fidelity | ✓ Good — higher precision |
| Separate tool for source report | Keeps concerns separated, allows generating report independently | ✓ Good — clean separation |
| SSRF Protection | Strict validation of URLs to block private/local network probes | ✓ Good — safety boundary |
| Pure red (#FF0000) for HALLUCINATED | Maximum visual distinction from NOT FOUND pink | ✓ Good — unmistakable warning |
| Server-side coverage enforcement | Reliability over LLM-only instructions | ✓ Good — guarantees report completeness |
| ComplianceService service layer | Extract all MCP tool logic into reusable service; shared by server and batch CLI | ✓ Good — no duplication |
| ProcessingContext state isolation | Fresh Pydantic model per model run in batch loop | ✓ Good — prevents state leakage |
| ScoreValue as Literal strings | "1i" cannot be integer; all 5 score values are strings: "1","1i","2","3","4" | ✓ Good — type-safe |
| JSON fence stripping in audit parser | LLMs frequently wrap output in markdown code fences; strip defensively | ✓ Good — robust parsing |
| Count-validation after parsing | Assert `len(field_audits) == len(questions)` to catch LLM skipping entries early | ✓ Good — catches format errors |
| Repeat section name in xlsx rows | Keeps data filterable/sortable in Excel vs cell merge | ✓ Good — usable spreadsheet |
| SECTION_MAP single source of truth in generate_report | Imported from report_generator, not redefined — prevents drift | ✓ Good — zero duplication |
| `(df, has_data)` tuple return for question_problem_table | Explicit bool cleaner than None-check for optional table render | ✓ Good — clear empty-data path |
| `(df, footnote)` tuple for make_table6 | Keeps footnote out of DataFrame so raw CSV has clean numeric data | ✓ Good — clean exports |
| Commentary from formatted DataFrames | Derives from output strings to avoid redundant recomputation | ✓ Good — single pass |
| Smoke assertions in `run()` | Fail-fast if batch_report.md is empty or missing headers | ✓ Good — catches silent failures |

---
*Last updated: 2026-03-03 after v1.5 milestone*
