# EU AI Act Compliance MCP Server

## What This Is

An MCP server that helps users generate EU AI Act Article 53 GPAI compliance documentation from Hugging Face model cards. Claude fetches and enriches model card data, answers 50+ compliance questions, generates a downloadable Word document, and produces a companion PDF source citation report tracking the provenance and confidence of every answer. Deployed on Railway and usable from Claude Desktop or Claude.ai.

## Core Value

Every answer in the compliance document must be traceable back to its source — users need to trust and verify the generated compliance form.

## Requirements

### Validated

- ✓ Fetch and enrich HuggingFace model cards with linked papers/docs — existing
- ✓ Expose 50+ EU AI Act compliance questions via MCP tool — existing
- ✓ Generate DOCX compliance document from template with placeholder substitution — existing
- ✓ Serve generated documents via download endpoint with 24-hour retention — existing
- ✓ Deploy via Railway with persistent volume storage — existing
- ✓ Support Claude Desktop (stdio) and Claude.ai (HTTP/SSE) connections — existing
- ✓ CORS handling for cross-origin MCP clients — existing
- ✓ Background cleanup of expired documents — existing
- ✓ Capture source citations during compliance form generation (quote, section, confidence level per answer) — v1.1
- ✓ New `generate_source_report` MCP tool that produces a PDF source citation report — v1.1
- ✓ PDF report shows for each field: question ID, answer, source location (section + quote), confidence level — v1.1
- ✓ Inference chains for non-direct answers: related quote(s) + reasoning that led to the answer — v1.1
- ✓ PDF generated server-side using ReportLab — v1.1
- ✓ PDF served via same download endpoint as DOCX files — v1.1

### Active

- [ ] HALLUCINATED confidence level — new 5th type for answers not supported by model card sources, with self-checking during source report generation
- [ ] Automatic source report workflow — Claude must call `generate_source_report` immediately after `generate_compliance_doc`, presenting both links together
- [ ] Full question coverage — every question in questions.json must appear in the source report, even if NOT FOUND

## Current Milestone: v1.2 Source Report Reliability

**Goal:** Make source citation reports trustworthy by ensuring full coverage, detecting hallucinations, and automating the generation flow.

**Target features:**
- HALLUCINATED confidence level with self-verification against model card
- Automatic end-to-end workflow (compliance doc + source report together)
- Mandatory citation for all 50+ compliance questions

### Out of Scope

- Modifying the existing DOCX template structure — not needed for source tracking
- Real-time validation during form fill — source report is post-generation
- Embedding citations directly into the DOCX — separate PDF report is cleaner
- Authentication/authorization — not addressed yet
- PDF/A archival format — verify regulatory requirements before investing effort
- Multi-source reconciliation — deferred to v2
- Change tracking across compliance form versions — deferred to v2
- Auditor annotation space — deferred to v2

## Context

Shipped v1.1 with 2,279 LOC Python (57 tests passing).
Tech stack: Python 3.10+, FastMCP, python-docx, ReportLab 4.4.10, Pydantic v2, DejaVu Sans font family.
Deployed on Railway with persistent volume storage.

**Architecture:** FastMCP server with 4 tools (`fetch_hf_model_card`, `get_compliance_requirements`, `generate_compliance_doc`, `generate_source_report`) and 2 resources. Document generation uses python-docx for DOCX and ReportLab for PDF. Files stored in `DATA_DIR` with 24-hour TTL cleanup handling both .docx and .pdf files.

**Workflow:** User provides model ID -> Claude fetches model card -> Claude answers compliance questions while tracking source citations -> Claude calls `generate_compliance_doc` (DOCX) -> Claude calls `generate_source_report` (PDF) -> User gets both documents.

**Confidence levels:**
- **DIRECT** — Answer directly quoted from model card (verbatim quote + section, displayed in italics)
- **INFERRED** — Answer derived from related information (related quote(s) + reasoning chain)
- **DEFAULT** — Standard/assumed value used (explains why default was appropriate)
- **NOT FOUND** — Information not available in model card (documents what was searched for)
- **HALLUCINATED** — Answer not supported by model card sources (flagged during self-check) *(v1.2)*

**Known issues (v1.1):**
- Claude does not reliably call `generate_source_report` after `generate_compliance_doc` despite context.md instructions
- Source reports only cover ~26 of 50+ questions — incomplete coverage

## Constraints

- **Stack**: Python 3.10+, ReportLab for PDF, python-docx for DOCX
- **Deployment**: Railway with persistent volume mount for document storage
- **Cleanup**: 24-hour TTL cleanup thread handles both .docx and .pdf files
- **MCP Protocol**: All tools follow `@mcp.tool()` patterns
- **Dependencies**: Minimal — ReportLab is the only dependency added in v1.1

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Separate tool for source report (not combined with DOCX generation) | Keeps concerns separated, allows generating report independently, doesn't break existing DOCX workflow | Good — clean separation, independent generation works well |
| Source data as separate JSON parameter (not embedded in compliance data) | Clean separation between answers and their provenance metadata | Good — Pydantic validation catches errors before PDF generation |
| ReportLab for PDF generation | Pure Python, no system dependencies, well-maintained, sufficient for structured reports | Good — handles Unicode, tables, multi-page well |
| Confidence levels: DIRECT/INFERRED/DEFAULT/NOT FOUND | Matches the user's existing validation prompt categories, covers all source types | Good — clear semantic distinction, maps well to visual formatting |
| DejaVu Sans font for Unicode rendering | Open-source, supports European languages and common Unicode symbols | Good — prevents encoding crashes |
| WCAG AA compliant confidence colors | Accessible color coding with 4.5:1+ contrast ratio | Good — works in print and on screen |
| context.md workflow guidance instead of code changes | System prompt modification enables workflow changes without code changes | Good — faster iteration, matches existing patterns |
| 3-phase structure (merged scale testing) | 25 requirements extending existing system, 3 phases optimal delivery | Good — completed efficiently in single day |

---
*Last updated: 2026-02-16 after v1.2 milestone started*
