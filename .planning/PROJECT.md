# EU AI Act Compliance MCP Server

## What This Is

An MCP server that helps users generate EU AI Act Article 53 GPAI compliance documentation from Hugging Face model cards. Claude fetches and enriches model card data, answers 50+ compliance questions, and generates a downloadable Word document. Deployed on Railway and usable from Claude Desktop or Claude.ai.

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

### Active

- [ ] Capture source citations during compliance form generation (quote, section, confidence level per answer)
- [ ] New `generate_source_report` MCP tool that produces a PDF source citation report
- [ ] PDF report shows for each field: question ID, answer, source location (section + quote), confidence level (DIRECT/INFERRED/DEFAULT/NOT FOUND)
- [ ] Inference chains for non-direct answers: related quote(s) + reasoning that led to the answer
- [ ] PDF generated server-side using ReportLab
- [ ] PDF served via same download endpoint as DOCX files

### Out of Scope

- Modifying the existing DOCX template structure — not needed for source tracking
- Real-time validation during form fill — source report is post-generation
- Embedding citations directly into the DOCX — separate PDF report is cleaner
- Authentication/authorization — not part of this milestone

## Context

**Existing architecture:** FastMCP server with 3 tools (`fetch_hf_model_card`, `get_compliance_requirements`, `generate_compliance_doc`) and 2 resources. Document generation uses python-docx template filling. Files stored in `DATA_DIR` with 24-hour TTL cleanup.

**Current workflow:** User provides model ID → Claude fetches model card → Claude answers compliance questions → Claude calls `generate_compliance_doc` with JSON answers → Server fills DOCX template → Returns download link.

**New workflow addition:** After generating DOCX, Claude calls `generate_source_report` with source citation JSON → Server generates PDF using ReportLab → Returns download link. The source citation JSON is a separate parameter containing per-field metadata (source quote, section heading, confidence level, inference reasoning).

**Confidence levels:**
- **DIRECT** — Answer directly quoted from model card (include exact quote + section)
- **INFERRED** — Answer derived from related information (include related quote(s) + reasoning chain)
- **DEFAULT** — Standard/assumed value used (explain why default was appropriate)
- **NOT FOUND** — Information not available in model card (note what was searched for)

**Key technical consideration:** The source citation data is structured by Claude during the compliance form generation step. The `generate_source_report` tool receives this pre-structured data — it doesn't re-analyze the model card.

## Constraints

- **Stack**: Python 3.10+, ReportLab for PDF generation — matches existing Python stack
- **Deployment**: Must work on Railway with same volume mount for PDF storage
- **Cleanup**: PDFs must be handled by existing 24-hour cleanup thread (extend to .pdf files)
- **MCP Protocol**: New tool must follow existing `@mcp.tool()` patterns
- **Dependencies**: ReportLab is the only new dependency — keep it minimal

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Separate tool for source report (not combined with DOCX generation) | Keeps concerns separated, allows generating report independently, doesn't break existing DOCX workflow | — Pending |
| Source data as separate JSON parameter (not embedded in compliance data) | Clean separation between answers and their provenance metadata | — Pending |
| ReportLab for PDF generation | Pure Python, no system dependencies, well-maintained, sufficient for structured reports | — Pending |
| Confidence levels: DIRECT/INFERRED/DEFAULT/NOT FOUND | Matches the user's existing validation prompt categories, covers all source types | — Pending |

---
*Last updated: 2026-02-15 after initialization*
