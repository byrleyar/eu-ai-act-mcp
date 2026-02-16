# EU AI Act Compliance MCP Server

## What This Is

An MCP server that helps users generate EU AI Act Article 53 GPAI compliance documentation from Hugging Face model cards. Claude fetches and enriches model card data, answers 50+ compliance questions, generates a downloadable Word document, and produces a companion PDF source citation report tracking the provenance and confidence of every answer. Deployed on Railway and usable from Claude Desktop or Claude.ai.

## Core Value

Every answer in the compliance document must be traceable back to its source — users need to trust and verify the generated compliance form.

## Current State

**Shipped v1.3** -- 2026-02-16
**Stats:** 3,100+ LOC Python, 77 tests passing.
**Key Accomplishments:**
- ✓ **High-Fidelity Data Acquisition**: Targeted discovery and retrieval of technical documentation to fill data gaps.
- ✓ **Agentic Retrieval Workflow**: Active investigation loop (Gap Analysis -> Targeted Fetch) for higher fidelity reports.
- ✓ **Discovery Engine Overhaul**: Automated extraction of links from BibTeX, citation blocks, and repo file lists.
- ✓ **Targeted Fetch Tool**: On-demand retrieval and parsing of academic papers with SSRF protection.

## Roadmap

<details>
<summary>v1.3 High-Fidelity Data Acquisition (Shipped 2026-02-16)</summary>

**Goal:** Enable targeted discovery and retrieval of technical documentation to fill data gaps in compliance reports.

- [x] On-demand PDF/Doc retrieval tool
- [x] Discovery engine overhaul (BibTeX, Citations, Repo files)
- [x] Agentic retrieval workflow (Gap Analysis -> Targeted Fetch)

See [.planning/milestones/v1.3-ROADMAP.md](milestones/v1.3-ROADMAP.md) for full archive.

</details>

<details>
<summary>v1.2 Source Report Reliability (Shipped 2026-02-16)</summary>

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

## Next Milestone Goals (v1.4 Proposed)

- **Audit & Review Workflow**: Allow users to "approve" or "comment" on citations in a third step.
- **Regulatory Mapping**: Link each question ID to specific articles and measures in the EU AI Act.
- **Enhanced Document Linkage**: Embed source report links or QR codes directly in the DOCX compliance form.

## Context

Tech stack: Python 3.10+, FastMCP, python-docx, ReportLab 4.4.10, Pydantic v2, DejaVu Sans font family.
Deployed on Railway with persistent volume storage.

**Architecture:** FastMCP server with tools for model card fetching, requirements retrieval, and document generation (DOCX/PDF). Supports targeted document retrieval via `fetch_external_document`.

**Workflow:** User provides model ID -> Claude fetches model card and link checklist -> Claude performs gap analysis -> Claude fetches specific missing docs -> Claude generates compliance form and source report.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Agentic Retrieval | Shift from "fetch everything" to "fetch what is missing" to optimize context usage and fidelity | Good — higher precision |
| Separate tool for source report | Keeps concerns separated, allows generating report independently | Good — clean separation |
| SSRF Protection | Strict validation of URLs to block private/local network probes | Good — safety boundary |
| Pure red (#FF0000) for HALLUCINATED | Maximum visual distinction from NOT FOUND pink | Good — unmistakable warning |
| Server-side coverage enforcement | Reliability over LLM-only instructions | Good — guarantees report completeness |

---
*Last updated: 2026-02-16 after Milestone v1.3 complete*
