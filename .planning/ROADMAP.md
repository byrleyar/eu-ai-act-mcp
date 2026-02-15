# Roadmap: Source Citation Reports

**Milestone:** EU AI Act Compliance MCP Server - Source Citation Reports
**Created:** 2026-02-15
**Depth:** Standard (3 phases)

## Overview

This roadmap delivers PDF-based source citation reporting for the EU AI Act compliance MCP server. Each phase builds on working infrastructure to add independent, testable capabilities. The structure follows the existing architecture pattern: foundation infrastructure first, then MCP integration mirroring existing tools, then feature completeness for audit readiness.

## Phases

### Phase 1: PDF Infrastructure & Data Model

**Goal:** Users can generate structurally sound PDF reports with validated citation data.

**Dependencies:** None (foundation phase)

**Plans:** 2 plans

Plans:
- [x] 01-01-PLAN.md -- Citation data model and Pydantic schema validation (DATA-01, DATA-02, DATA-03)
- [x] 01-02-PLAN.md -- PDF generator with ReportLab, DejaVu Sans font, and unit tests (INFRA-01, INFRA-02, INFRA-03, INFRA-04)

**Requirements Covered:**
- INFRA-01: Unicode-compatible font prevents encoding crashes
- INFRA-02: In-memory PDF generation using BytesIO buffer
- INFRA-03: Auto-wrapping table layout handles variable-length text
- INFRA-04: Multi-page PDFs repeat header rows
- DATA-01: Citation JSON schema definition
- DATA-02: Confidence level support (DIRECT/INFERRED/DEFAULT/NOT FOUND)
- DATA-03: Schema validation with clear error messages

**Success Criteria:**
1. PDF generator function accepts citation JSON and BytesIO stream, produces valid PDF without file I/O
2. DejaVu Sans font registration prevents Unicode encoding failures on special characters (smart quotes, em-dashes, non-Latin scripts)
3. Table layout auto-wraps text content exceeding 1000 characters without overflow or data loss
4. Multi-page reports repeat header rows on each page for readability
5. Pydantic schema validation rejects malformed citation JSON (nulls, wrong types, missing fields) with specific error messages explaining the issue
6. Unit tests verify PDF generation with mock citation data containing edge cases (very long quotes, special characters, all confidence levels)

**Rationale:** PDF generation patterns (fonts, layouts, validation) are architectural decisions affecting all subsequent phases. Building citation features on fragile infrastructure leads to costly rework. This phase addresses the critical pitfalls identified in research: Unicode encoding, variable-length overflow, and schema validation.

---

### Phase 2: MCP Tool Integration & File Management

**Goal:** Users can call a new MCP tool to generate source reports and download PDFs with automatic cleanup.

**Dependencies:** Phase 1 (pdf_generator.py module must exist)

**Plans:** 2 plans

Plans:
- [x] 02-01-PLAN.md -- Implement generate_source_report MCP tool and extend cleanup for PDFs (TOOL-01, TOOL-02, TOOL-03, TOOL-04, FILE-01, FILE-02, FILE-03)
- [x] 02-02-PLAN.md -- Integration tests for MCP tool and file management verification

**Requirements Covered:**
- TOOL-01: New `generate_source_report` MCP tool with `source_citations_json` parameter
- TOOL-02: Tool parses JSON, validates schema, calls PDF generator, saves to DATA_DIR
- TOOL-03: Tool returns TextContent + EmbeddedResource (mirrors `generate_compliance_doc` pattern)
- TOOL-04: PDF filename includes model name and `_sources_` suffix with UUID
- FILE-01: PDFs stored in DATA_DIR alongside DOCX files
- FILE-02: Cleanup thread extended to handle .pdf files with 24-hour TTL
- FILE-03: Download route serves PDFs with correct Content-Type

**Success Criteria:**
1. `generate_source_report` tool appears in MCP tool schema and accepts source_citations_json string parameter
2. Tool validates citation JSON using Pydantic schema from Phase 1 before generation
3. Generated PDF saved to DATA_DIR with filename format `{ModelName}_sources_{uuid}.pdf`
4. Tool returns both TextContent (download link) and EmbeddedResource (base64 PDF) matching existing `generate_compliance_doc` pattern
5. Cleanup thread deletes both .docx and .pdf files older than 24 hours
6. Download endpoint serves PDF files with Content-Type `application/pdf` and supports browser download
7. Railway deployment serves PDFs via public URL (RAILWAY_PUBLIC_DOMAIN or RAILWAY_STATIC_URL)

**Rationale:** MCP integration follows the proven `generate_compliance_doc` pattern exactly, minimizing implementation risk. File management extends existing cleanup logic with minimal changes. This phase validates the end-to-end flow (JSON -> PDF -> download URL) before adding feature complexity.

---

### Phase 3: Citation Features & Workflow

**Goal:** Users can generate audit-ready source citation reports with visual hierarchy, confidence indicators, and executive summaries.

**Dependencies:** Phase 2 (MCP tool and file management must work)

**Plans:** 2 plans

Plans:
- [ ] 03-01-PLAN.md -- Enhanced PDF with confidence colors, citation hierarchy, executive summary, and footer (CITE-01 through CITE-09)
- [ ] 03-02-PLAN.md -- Workflow integration (context.md) and comprehensive testing (FLOW-01, FLOW-02)

**Requirements Covered:**
- CITE-01: Citation entries display question ID, question text, and answer
- CITE-02: DIRECT citations show verbatim source quote with section attribution
- CITE-03: INFERRED citations show related quotes and reasoning chain
- CITE-04: DEFAULT citations explain why standard value was used
- CITE-05: NOT FOUND citations note what was searched for
- CITE-06: Confidence level visual encoding (color + text label)
- CITE-07: Executive summary with confidence breakdown and source count
- CITE-08: Cross-references use question IDs from questions.json
- CITE-09: Report includes generation timestamp and model card identifier
- FLOW-01: context.md updated to instruct Claude to track source citations
- FLOW-02: Claude can call `generate_source_report` independently

**Success Criteria:**
1. Each citation entry clearly displays question ID, question text, and answer in hierarchical layout
2. DIRECT confidence citations show verbatim source quote in italics with section heading attribution
3. INFERRED confidence citations show related quote(s) plus reasoning chain explaining derivation
4. DEFAULT confidence citations explain why a standard/assumed value was appropriate for this context
5. NOT FOUND confidence citations document what information was searched for but not located
6. Confidence levels displayed with both color coding and text labels (accessible in grayscale print)
7. Executive summary section shows confidence breakdown (count per level), total questions answered, and sources consulted
8. Question IDs match those in questions.json to enable cross-referencing with compliance form
9. Report footer includes generation timestamp and model card identifier for traceability
10. context.md instructs Claude to track source citations during compliance form generation and call `generate_source_report` after `generate_compliance_doc`

**Rationale:** With infrastructure solid and MCP integration working, this phase adds table stakes features that make the report audit-ready. Focus is on visual hierarchy, confidence display, and source attribution. Features are independent and can be iterated rapidly without touching core generation logic.

---

## Progress

| Phase | Status | Requirements | Started | Completed |
|-------|--------|--------------|---------|-----------|
| 1 - PDF Infrastructure & Data Model | ✓ Complete | 7 | 2026-02-15 | 2026-02-15 |
| 2 - MCP Tool Integration & File Management | ✓ Complete | 7 | 2026-02-15 | 2026-02-15 |
| 3 - Citation Features & Workflow | Planned | 11 | - | - |

**Total:** 25 requirements across 3 phases

## Phase Ordering Rationale

**Infrastructure-first approach:** PDF generation patterns (fonts, layouts, validation) are architectural decisions that affect all subsequent phases. Building citation features on top of fragile infrastructure leads to costly rework. Phase 1 addresses the critical pitfalls identified in research (Unicode encoding, variable-length overflow, schema validation) before any integration work begins.

**MCP integration before features:** Proving the end-to-end flow (JSON -> PDF -> download URL) validates the architecture before adding feature complexity. Phase 2 follows the existing project pattern (DOCX generator is simple, reliable, testable) by directly replicating the `generate_compliance_doc` pattern.

**Features after integration:** Visual design (confidence encoding, citation formatting) is easier to iterate once the pipeline works. Phase 3 separates infrastructure from presentation, allowing rapid iteration on UX without touching core generation logic. This phase delivers audit-ready formatting and workflow integration.

**Efficiency through merging:** Research suggested 4 phases (Infrastructure, Integration, Features, Scale Testing), but we merged Scale Testing into Phase 2 validation criteria and deployment verification. For a project of this scope (25 requirements, adding to existing working system), 3 phases provides optimal delivery cadence without artificial splits.

## Research Integration

This roadmap incorporates research findings:

- **Phase 1** addresses all 6 critical pitfalls identified: Unicode encoding, variable-length overflow, confidence visualization, URL handling, memory management, schema validation
- **Phase 2** follows the recommended "MCP tool as orchestration boundary" and "generator as pure function" patterns from architecture research
- **Phase 3** implements table stakes features (question-to-source mapping, verbatim quotes, confidence indicators) identified in feature research, deferring competitive features (multi-source reconciliation, change tracking) to v2

**Research flags addressed:**
- ReportLab version verification occurs in Phase 1 setup
- Railway container limits tested during Phase 2 deployment
- Font licensing verified (DejaVu Sans is open-source)
- PDF/A compliance deferred to user validation (marked out-of-scope)

---

*Roadmap created: 2026-02-15*
*Last updated: 2026-02-15 after phase 3 planning*
