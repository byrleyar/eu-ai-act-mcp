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

**Phase:** Phase 3 - Citation Features & Workflow
**Plan:** 03-03 complete
**Status:** In progress

**Progress:**
```
[██████████] 100% (7/7 plans complete overall)

Phase 1: PDF Infrastructure & Data Model ██████████ 7/7 ✓
Phase 2: MCP Tool Integration & File Management ██████████ 7/7 ✓
Phase 3: Citation Features & Workflow ██████████ 11/11 ✓ (all plans complete)
```

## Performance Metrics

**Milestone started:** 2026-02-15
**Milestone completed:** 2026-02-15
**Phases completed:** 3/3
**Requirements completed:** 25/25 (DATA-01 through DATA-03, INFRA-01 through INFRA-04, TOOL-01 through TOOL-04, FILE-01 through FILE-03, TEST-01 through TEST-03, CITE-01 through CITE-09, FLOW-01 through FLOW-02)
**Current phase progress:** Phase 3 complete — all requirements delivered

**Velocity:** Established

| Phase | Plan | Duration | Tasks | Files | Completed |
|-------|------|----------|-------|-------|-----------|
| 01    | 01   | 7min     | 2     | 4     | 2026-02-15 |
| 01    | 02   | 4min     | 2     | 4     | 2026-02-15 |
| 02    | 01   | 2min     | 2     | 1     | 2026-02-15 |
| 02    | 02   | 2min     | 2     | 1     | 2026-02-15 |
| 03    | 01   | 3min     | 2     | 2     | 2026-02-15 |
| 03    | 02   | 2min     | 2     | 2     | 2026-02-15 |
| 03    | 03   | 5min     | 2     | 6     | 2026-02-15 |

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

---

**Date:** 2026-02-15
**Decision:** Use pytest fixtures with yield pattern for test cleanup
**Rationale:** Fixtures provide better isolation and automatic cleanup even when tests fail. cleanup_pdfs fixture yields before cleanup, allowing test to run first. More idiomatic pytest pattern than manual cleanup in each test.

---

**Date:** 2026-02-15
**Decision:** Test infrastructure via source inspection rather than execution
**Rationale:** Used inspect.getsource(cleanup_old_files) to verify .pdf handling. Avoids running actual cleanup thread which could interfere with test files. Safer approach than waiting for cleanup to execute or mocking time.

---

**Date:** 2026-02-15
**Decision:** Verify PDF validity with magic bytes check
**Rationale:** Base64 decode blob and check for %PDF header. Proves the embedded resource contains valid PDF data, not just random bytes. Simple, reliable validation without full PDF parsing.

---

**Date:** 2026-02-15
**Decision:** Use WCAG AA compliant colors for confidence level visualization
**Rationale:** Ensures 4.5:1+ contrast ratio with black text for accessibility. Light green (#D4EDDA) for DIRECT, light yellow (#FFF3CD) for INFERRED, light gray (#E7E8EA) for DEFAULT, light red (#F8D7DA) for NOT FOUND provides intuitive color coding that meets accessibility standards.

---

**Date:** 2026-02-15
**Decision:** Format citation content differently per confidence type
**Rationale:** Different confidence levels represent fundamentally different citation patterns. DIRECT citations have verbatim quotes worthy of italic emphasis; INFERRED citations need reasoning chain display; DEFAULT citations need rationale explanation; NOT FOUND citations document search attempts. Tailored formatting makes each type immediately recognizable.

---

**Date:** 2026-02-15
**Decision:** Use question_id in first table column for cross-referencing
**Rationale:** Enables cross-referencing between PDF report and questions.json. Auditors can trace specific questions back to schema definition. Maintains stable identifiers across report regenerations.

---

**Date:** 2026-02-15
**Decision:** Increase bottom margin to 0.75 inch to accommodate footer
**Rationale:** Default 0.5 inch margin didn't leave sufficient space for footer without overlapping table content. 0.75 inch provides comfortable buffer for 8pt footer text at 0.3 inch from bottom.

---

**Date:** 2026-02-15
**Decision:** Use context.md system prompt to guide citation tracking workflow
**Rationale:** System prompt modification enables workflow changes without code changes. Mirrors existing "do not interview the user" pattern. Provides Claude with concrete examples and clear confidence level definitions. Faster iteration than implementing citation tracking logic in Python.

---

**Date:** 2026-02-15
**Decision:** Provide complete JSON example with DIRECT and NOT FOUND citations
**Rationale:** Demonstrates schema with two contrasting confidence levels. DIRECT shows full citation with quote and section; NOT FOUND shows empty optional fields with reasoning documenting search attempt. Example matches actual Pydantic schema fields from citation_schema.py.

---

**Date:** 2026-02-15
**Decision:** Add semantic verification tests for CITE-03 and CITE-04
**Rationale:** Presence tests verify fields exist; semantic tests verify reasoning content explains WHY. CITE-03 requires INFERRED citations show derivation chain; CITE-04 requires DEFAULT citations explain why standard value is appropriate. Content quality matters for audit trail value.

---

**Date:** 2026-02-15
**Decision:** Widen PDF table # column from 0.3" to 0.7" to support long question IDs
**Rationale:** Question IDs like "training_data_sources" (21 chars) wrapped across 7+ lines at 0.3" width. At 8pt font, 0.7" supports ~21 characters, reducing wrapping to 1-2 lines max. Redistributed space from Source Quote (2.0"→1.8") and Section (0.6"→0.5") columns while maintaining 7.5" total width within page margins.

---

**Date:** 2026-02-15
**Decision:** Use DejaVu Sans font family for italic support
**Rationale:** ReportLab's registerFontFamily enables automatic italic rendering when <i> tags are used in Paragraph markup, providing seamless integration without manual font switching. Downloaded DejaVuSans-Oblique.ttf from official release to enable professional typography for DIRECT citation quotes.

---

**Date:** 2026-02-15
**Decision:** Make source_document optional with empty string default
**Rationale:** Maintains backward compatibility with existing citations while enabling future source tracking. Empty string is more natural than None for optional text fields in Pydantic. Allows tracking which document (model card, PDF attachment, user context) contained each quote without breaking existing code.

---

**Date:** 2026-02-15
**Decision:** Only display "Document:" line when source_document is non-empty
**Rationale:** Prevents cluttering PDF with empty fields. Conditional formatting keeps output clean when source tracking isn't used while providing valuable attribution when it is.

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
- ✅ Write comprehensive integration tests for generate_source_report tool (02-02 complete - 16 tests)
- ✅ Test edge cases: Unicode, long text, multi-citation, error handling (02-02 complete)
- ✅ Validate all 7 Phase 2 requirements through automated tests (02-02 complete)
- ✅ Phase 2 complete - all requirements verified

**Phase 3 - Citation Features & Workflow:**
- ✅ Add confidence colors and executive summary to PDF generator (03-01 complete)
- ✅ Implement hierarchical citation display per confidence type (03-01 complete)
- ✅ Add page footer with model card ID and timestamp (03-01 complete)
- ✅ Pass model_card_id parameter through MCP tool (03-01 complete)
- ✅ Apply WCAG AA compliant confidence-based row coloring (03-01 complete)
- ✅ Update context.md with citation tracking workflow instructions (03-02 complete)
- ✅ Add comprehensive tests for all Phase 3 citation features (03-02 complete)
- ✅ Phase 3 complete - all requirements verified

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

**Timestamp:** 2026-02-15T18:35:00Z
**Stopped at:** Completed 03-03-PLAN.md (italic font support and source_document tracking)
**Next action:** Continue with remaining Phase 3 plans if any, or mark milestone complete.

---

*State tracking for: Source Citation Reports milestone*
*Created: 2026-02-15*
*Last updated: 2026-02-15 after 03-03 completion*
