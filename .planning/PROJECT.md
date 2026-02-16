# EU AI Act Compliance MCP Server

## What This Is

An MCP server that helps users generate EU AI Act Article 53 GPAI compliance documentation from Hugging Face model cards. Claude fetches and enriches model card data, answers 50+ compliance questions, generates a downloadable Word document, and produces a companion PDF source citation report tracking the provenance and confidence of every answer. Deployed on Railway and usable from Claude Desktop or Claude.ai.

## Core Value

Every answer in the compliance document must be traceable back to its source — users need to trust and verify the generated compliance form.

## Current State

**Shipped v1.2** -- 2026-02-16
**Stats:** 2,750+ LOC Python, 67 tests passing.
**Key Accomplishments:**
- ✓ **Hallucination Detection**: `HALLUCINATED` confidence level with bold red visual treatment in PDF.
- ✓ **Full Coverage**: Mandatory citation for all 80+ compliance questions enforced on server.
- ✓ **Workflow Automation**: Just-in-time enforcement in `server.py` and `context.md` for reliable two-step tool execution.
- ✓ **Self-Verification Protocol**: Claude audits its own answers against source text before report generation.

## Roadmap

<details>
<summary>v1.2 Source Report Reliability (Shipped 2026-02-16)</summary>

**Goal:** Make source citation reports trustworthy by ensuring full coverage, detecting hallucinations, and automating the generation flow.

- [x] HALLUCINATED confidence level with self-verification against model card
- [x] Automatic end-to-end workflow (compliance doc + source report together)
- [x] Mandatory citation for all 80+ compliance questions enforced via server-side validation

See [.planning/milestones/v1.2-ROADMAP.md](milestones/v1.2-ROADMAP.md) for full archive.

</details>

<details>
<summary>v1.1 Source Citation Reports (Shipped 2026-02-15)</summary>

- [x] Capture source citations during compliance form generation (quote, section, confidence level per answer)
- [x] New `generate_source_report` MCP tool that produces a PDF source citation report
- [x] PDF report shows for each field: question ID, answer, source location (section + quote), confidence level
- [x] Inference chains for non-direct answers: related quote(s) + reasoning that led to the answer

See [.planning/milestones/v1.1-ROADMAP.md](milestones/v1.1-ROADMAP.md) for full archive.

</details>

## Next Milestone Goals (v1.3 Proposed)

- **Audit & Review Workflow**: Allow users to "approve" or "comment" on citations in a third step.
- **Regulatory Mapping**: Link each question ID to specific articles and measures in the EU AI Act.
- **Enhanced Document Linkage**: Embed source report links or QR codes directly in the DOCX compliance form.

## Context

Tech stack: Python 3.10+, FastMCP, python-docx, ReportLab 4.4.10, Pydantic v2, DejaVu Sans font family.
Deployed on Railway with persistent volume storage.

**Architecture:** FastMCP server with 4 tools (`fetch_hf_model_card`, `get_compliance_requirements`, `generate_compliance_doc`, `generate_source_report`) and 2 resources. Document generation uses python-docx for DOCX and ReportLab for PDF. Files stored in `DATA_DIR` with 24-hour TTL cleanup handling both .docx and .pdf files.

**Workflow:** User provides model ID -> Claude fetches model card -> Claude answers compliance questions while tracking source citations -> Claude calls `generate_compliance_doc` (DOCX) -> Claude calls `generate_source_report` (PDF) -> User gets both documents.

**Confidence levels:**
- **DIRECT** — Answer directly quoted from model card (italics)
- **INFERRED** — Answer derived from related information (related quote + reasoning)
- **DEFAULT** — Standard/assumed value used (rationale provided)
- **NOT FOUND** — Information not available in model card (searched areas documented)
- **HALLUCINATED** — Answer not supported by sources (bold red warning, flagged during self-check)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Separate tool for source report | Keeps concerns separated, allows generating report independently | Good — clean separation |
| Source data as separate JSON parameter | Clean separation between answers and their provenance metadata | Good — Pydantic validation catches errors |
| Pure red (#FF0000) for HALLUCINATED | Maximum visual distinction from NOT FOUND pink | Good — unmistakable warning |
| Server-side coverage enforcement | Reliability over LLM-only instructions | Good — guarantees report completeness |
| Just-in-time workflow instructions in server.py | Acts as a state machine trigger to prevent stopping halfway | Good — ensures 2nd tool call is made |

---
*Last updated: 2026-02-16 after Milestone v1.2 complete*
