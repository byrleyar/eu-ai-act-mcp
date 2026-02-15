# Project State

**Project:** EU AI Act Compliance MCP Server
**Milestone:** Source Citation Reports
**Last Updated:** 2026-02-15

## Project Reference

### Core Value
Every answer in the compliance document must be traceable back to its source — users need to trust and verify the generated compliance form.

### Current Focus
Adding PDF-based source citation reporting to enable audit trails. The system currently generates DOCX compliance forms; this milestone adds companion PDF reports that track sources, confidence levels, and reasoning for each answer.

## Current Position

**Phase:** Phase 2 - MCP Tool Integration & File Management (in progress)
**Plan:** 02-01 complete, continuing Phase 2
**Status:** Phase 2 started — 1/2 plans complete

**Progress:**
```
[████████░░░░░░░░░░░░] 40% (10/25 requirements complete)

Phase 1: PDF Infrastructure & Data Model ██████████ 7/7 ✓
Phase 2: MCP Tool Integration & File Management ████░░░░░░ 3/7
Phase 3: Citation Features & Workflow ░░░░░░░░░░ 0/11
```

## Performance Metrics

**Milestone started:** 2026-02-15
**Phases completed:** 1/3
**Requirements completed:** 10/25 (DATA-01, DATA-02, DATA-03, INFRA-01, INFRA-02, INFRA-03, INFRA-04, TOOL-01, TOOL-02, FILE-01)
**Current phase progress:** Phase 2 started — 1/2 plans complete

**Velocity:** Established

| Phase | Plan | Duration | Tasks | Files | Completed |
|-------|------|----------|-------|-------|-----------|
| 01    | 01   | 7min     | 2     | 4     | 2026-02-15 |
| 01    | 02   | 4min     | 2     | 4     | 2026-02-15 |
| 02    | 01   | 2min     | 2     | 1     | 2026-02-15 |

## Accumulated Context

### Key Decisions Made

**Date:** 2026-02-15
**Decision:** Use 3-phase structure instead of 4 phases suggested in research
**Rationale:** Merged scale testing into Phase 2 validation criteria for efficiency. For 25 requirements extending existing working system, 3 phases provides optimal delivery cadence.

---

**Date:** 2026-02-15
**Decision:** Phase 1 focuses on infrastructure before features
**Rationale:** PDF generation patterns (fonts, layouts, validation) are architectural decisions affecting all subsequent work. Research identified 6 critical pitfalls that must be addressed in foundation phase to avoid costly rework.

---

**Date:** 2026-02-15
**Decision:** Use Pydantic field validators to reject whitespace-only strings beyond min_length checks
**Rationale:** Pydantic's min_length validator accepts whitespace strings like "   " since length > 0. Field validators with strip() check ensure semantic validation beyond syntactic constraints.

---

**Date:** 2026-02-15
**Decision:** Allow empty strings for answer, source_quote, and source_section in citation schema
**Rationale:** NOT FOUND confidence level represents questions with no source answer, requiring empty optional fields while maintaining required reasoning field.

---

**Date:** 2026-02-15
**Decision:** Format validation errors with field paths for citation JSON
**Rationale:** Error messages like "citations -> 0 -> confidence: Input should be 'DIRECT'..." pinpoint exact problem location in nested JSON, enabling users to fix issues without guessing.

---

**Date:** 2026-02-15
**Decision:** Use DejaVu Sans font for Unicode rendering in PDFs
**Rationale:** ReportLab's default fonts don't support Unicode characters like smart quotes, em-dashes, or accented letters. DejaVu Sans is open-source, widely compatible, and handles all European languages plus common Unicode symbols.

---

**Date:** 2026-02-15
**Decision:** Enable splitByRow=True on PDF tables for long text handling
**Rationale:** Without splitByRow, tables with tall cells cause LayoutError when cell height exceeds frame height. Enabling row splitting allows multi-page tables to break between rows cleanly.

---

**Date:** 2026-02-15
**Decision:** XML-escape all user text before ReportLab Paragraph wrapping
**Rationale:** ReportLab's Paragraph flowable uses XML markup parsing. User-provided text containing &, <, > characters crashes the parser. Using html.escape() prevents this without losing data.

---

**Date:** 2026-02-15
**Decision:** Use _sources_ infix in PDF filename to distinguish from compliance docs
**Rationale:** Compliance docs use {ModelName}_{uuid}.docx while source reports use {ModelName}_sources_{uuid}.pdf. The _sources_ infix makes file purpose clear in DATA_DIR listings and prevents filename collisions.

---

**Date:** 2026-02-15
**Decision:** Use standard base64.b64encode (not urlsafe_b64encode) for MCP EmbeddedResource
**Rationale:** Research findings showed MCP validation errors occur with urlsafe encoding. Standard base64 encoding matches generate_compliance_doc pattern and passes MCP validation.

---

**Date:** 2026-02-15
**Decision:** Extend cleanup_old_files using tuple form of endswith(('.docx', '.pdf'))
**Rationale:** Single cleanup thread handles all generated document types with same 24-hour TTL. Tuple form of endswith() is idiomatic Python for multiple extension checks, avoiding duplicate cleanup logic.

### Active TODOs

**Phase 1 - PDF Infrastructure & Data Model:**
- ✅ Create Pydantic models for citation JSON schema validation (01-01 complete)
- ✅ Write unit tests for citation schema validation (01-01 complete)
- ✅ Set up ReportLab dependency with DejaVu Sans font (01-02 complete)
- ✅ Implement `pdf_generator.py` with `generate_source_report(output_stream, citations)` function (01-02 complete)
- ✅ Build auto-wrapping table layout with splitByRow support (01-02 complete)
- ✅ Write unit tests for PDF generation with edge cases (01-02 complete - 12 tests)
- ✅ Verify ReportLab current version on PyPI (confirmed 4.4.10 in Feb 2026)
- Test memory usage with 50+ citation reports

**Phase 2 - MCP Tool Integration & File Management:**
- ✅ Implement generate_source_report MCP tool in server.py (02-01 complete)
- ✅ Extend cleanup thread to handle .pdf files (02-01 complete)
- ✅ Verify download endpoint serves PDFs with correct Content-Type (02-01 complete)
- Remaining Phase 2 tasks TBD in subsequent plans

**Phase 3 - Citation Features & Workflow:**
- (Blocked until Phase 2 complete)

### Known Blockers

None at milestone start.

### Research Flags

**For Phase 1:**
- LOW priority: ReportLab version verification (API is stable, just confirm current release)
- LOW priority: Font licensing confirmation (DejaVu Sans is open-source, but verify embedding rights)

**For Phase 2:**
- MEDIUM priority: Railway container memory limits (verify current limits with official docs, training data shows 512MB default)
- LOW priority: Railway public URL construction for PDFs (mirrors existing DOCX pattern)

**For Phase 3:**
- LOW priority: Accessibility requirements (if PDFs must be screen-reader accessible, investigate ReportLab's PDF/UA support)
- DEFERRED: PDF/A archival format compliance (marked out-of-scope, flag for user validation before Phase 3 if needed)

### Technical Debt

None at milestone start. Existing codebase is clean with established patterns to follow.

### Architecture Notes

**Existing patterns to follow:**
- Generator as pure function (take streams, no file I/O inside generator)
- MCP tool as orchestration boundary (Claude controls workflow)
- Unified file cleanup with extension filter (add .pdf to existing .docx logic)
- Return pattern: TextContent + EmbeddedResource (mirror `generate_compliance_doc`)

**Critical pitfalls to avoid (from research):**
1. Unicode encoding failures → Use DejaVu Sans font
2. Variable-length text overflow → Use splitByRow=True, auto-wrapping Paragraphs
3. Confidence visualization inconsistency → Redundant encoding (color + text label)
4. Source URL handling issues → Format as clickable links with truncation
5. Memory issues on Railway → Test with realistic data volumes
6. Missing schema validation → Pydantic models with defensive programming

## Session Continuity

**For next session:**

When resuming work on this milestone:
1. Check current position in ROADMAP.md
2. Review Phase 1 success criteria
3. Start with `/gsd:plan-phase 1` to create detailed implementation plan
4. Verify ReportLab current version before installing dependencies

**Quick context:**
- Milestone adds PDF source citation reports to existing EU AI Act compliance MCP server
- Core workflow: Claude tracks sources during Q&A → calls new `generate_source_report` tool → user gets PDF alongside existing DOCX
- Architecture: New `pdf_generator.py` module parallel to existing `docx_generator.py`, following same patterns
- First task: Build PDF infrastructure with Unicode handling, auto-wrapping layouts, and schema validation

---

## Last Session

**Timestamp:** 2026-02-15T13:39:00Z
**Stopped at:** Completed 02-01-PLAN.md (generate_source_report MCP tool integration)
**Next action:** Continue with Phase 2 remaining plans or Phase 3 planning

---

*State tracking for: Source Citation Reports milestone*
*Created: 2026-02-15*
*Last updated: 2026-02-15 after 02-01 completion*
