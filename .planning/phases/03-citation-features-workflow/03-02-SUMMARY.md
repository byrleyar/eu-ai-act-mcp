---
phase: 03-citation-features-workflow
plan: 02
subsystem: workflow-documentation
tags: [context-md, workflow-instructions, citation-tracking, testing, phase3-completion]

# Dependency graph
requires:
  - phase: 03-citation-features-workflow
    plan: 01
    provides: Enhanced PDF generation with visual formatting, confidence coloring, executive summary, and footer
provides:
  - Citation tracking workflow instructions in context.md with confidence level definitions
  - Complete JSON example matching citation_schema.py fields
  - Tool call sequence instructions (generate_compliance_doc then generate_source_report)
  - Comprehensive test coverage for all Phase 3 CITE requirements (11 new tests)
  - Semantic verification tests for INFERRED and DEFAULT citation reasoning
affects: [claude-workflow, audit-trail, citation-quality, phase-3-completion]

# Tech tracking
tech-stack:
  added: [collections.Counter import in tests]
  patterns: [Workflow instruction via system prompt, semantic content verification in tests]

key-files:
  created: []
  modified: [context.md, tests/test_pdf_generator.py]

key-decisions:
  - "Use context.md system prompt to guide Claude's citation tracking behavior rather than code changes"
  - "Provide complete JSON example with both DIRECT and NOT FOUND citations to demonstrate full schema"
  - "Add semantic verification tests (CITE-03, CITE-04) checking reasoning content quality, not just presence"
  - "Normalize whitespace in PDF text extraction tests to handle ReportLab line-breaking variations"

patterns-established:
  - "System prompt workflow guidance: Instruct Claude via context.md with concrete examples and confidence definitions"
  - "Semantic test verification: Assert reasoning content explains WHY (not just that it exists)"
  - "Whitespace-tolerant PDF assertions: Use ''.join(text.split()) for cross-line text matching"

# Metrics
duration: 2min
completed: 2026-02-15
---

# Phase 03 Plan 02: Citation Features Workflow

**Context.md instructions for citation tracking workflow and comprehensive test coverage for all Phase 3 visual formatting requirements**

## Performance

- **Duration:** 2 minutes
- **Started:** 2026-02-15T14:30:54Z
- **Completed:** 2026-02-15T14:32:55Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Added Citation Tracking section to context.md with three subsections: Track Your Sources, When to Generate Source Report, Why This Matters
- Defined 4 confidence levels (DIRECT, INFERRED, DEFAULT, NOT FOUND) with clear semantic definitions
- Provided complete JSON example showing all 7 citation fields with both DIRECT and NOT FOUND examples
- Instructed Claude to call generate_source_report immediately after generate_compliance_doc with model_card_id parameter
- Added 11 comprehensive tests covering all Phase 3 CITE requirements (executive summary, confidence breakdown, color constants, question_id cross-referencing, citation formats per confidence type, footer with model_card_id)
- Implemented semantic verification tests for CITE-03 (INFERRED reasoning shows derivation) and CITE-04 (DEFAULT reasoning explains why standard value is appropriate)
- All 54 tests pass (15 citation schema + 23 PDF generator + 16 source report tool)

## Task Commits

Each task was committed atomically:

1. **Task 1: Update context.md with citation tracking workflow instructions** - `b0d283f` (docs)
2. **Task 2: Add comprehensive tests for Phase 3 citation features** - `6e71303` (test)

## Files Created/Modified
- `context.md` - Added Citation Tracking section with workflow instructions, confidence definitions, JSON example, and tool call sequence
- `tests/test_pdf_generator.py` - Added 11 new tests verifying Phase 3 CITE requirements with semantic content assertions

## Decisions Made

**Decision:** Use context.md system prompt to guide citation tracking workflow
**Rationale:** System prompt modification enables workflow changes without code changes. Mirrors existing "do not interview the user" pattern. Provides Claude with concrete examples and clear confidence level definitions. Faster iteration than implementing citation tracking logic in Python.

**Decision:** Provide complete JSON example with DIRECT and NOT FOUND citations
**Rationale:** Demonstrates schema with two contrasting confidence levels. DIRECT shows full citation with quote and section; NOT FOUND shows empty optional fields with reasoning documenting search attempt. Example matches actual Pydantic schema fields from citation_schema.py.

**Decision:** Add semantic verification tests for CITE-03 and CITE-04
**Rationale:** Presence tests verify fields exist; semantic tests verify reasoning content explains WHY. CITE-03 requires INFERRED citations show derivation chain; CITE-04 requires DEFAULT citations explain why standard value is appropriate. Content quality matters for audit trail value.

**Decision:** Normalize whitespace in PDF text extraction tests
**Rationale:** ReportLab text extraction can break text across lines in unpredictable ways (e.g., "model_architecture" becomes "mo\ndel\n_ar\nchi\ntec\ntur\ne"). Using ''.join(text.split()) removes all whitespace for reliable matching without coupling to PDF layout engine.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed whitespace normalization in question_id test**
- **Found during:** Task 2 test execution
- **Issue:** Test assertion failed because PDF text extraction split "model_architecture" across multiple lines. Test expected exact string match but ReportLab breaks text at column boundaries.
- **Fix:** Changed from `assert 'model_architecture' in all_text` to `normalized = ''.join(all_text.split()); assert 'model_architecture' in normalized`. Removes all whitespace before matching.
- **Files modified:** tests/test_pdf_generator.py
- **Commit:** 6e71303 (included in Task 2 commit)

## Issues Encountered

None - implementation proceeded smoothly after whitespace normalization fix. All 54 tests pass.

## User Setup Required

None - workflow changes are internal to context.md instructions. No external service configuration, no environment variables, no dependency updates.

## Next Phase Readiness

**Phase 3 complete.** All requirements satisfied:

- FLOW-01: context.md contains citation tracking instructions with confidence definitions and JSON example ✓
- FLOW-02: context.md describes calling generate_source_report after generate_compliance_doc with model_card_id ✓
- CITE-01 through CITE-09: All citation requirements have test coverage ✓
- All 54 tests pass with zero regressions ✓

**Milestone deliverables:**
1. PDF infrastructure with Unicode, auto-wrapping, multi-page support (Phase 1) ✓
2. MCP tool integration with file management and cleanup (Phase 2) ✓
3. Visual formatting with confidence colors, executive summary, footer (Phase 3 Plan 01) ✓
4. Citation workflow instructions and comprehensive test coverage (Phase 3 Plan 02) ✓

System ready for production use. Claude will now:
- Track citations during compliance form generation
- Call generate_compliance_doc to create DOCX form
- Immediately call generate_source_report to create PDF citation report
- Return both documents to user for audit trail

## Self-Check: PASSED

All files and commits verified:
- FOUND: context.md (modified with Citation Tracking section)
- FOUND: tests/test_pdf_generator.py (modified with 11 new tests)
- FOUND: b0d283f (Task 1 commit - context.md workflow instructions)
- FOUND: 6e71303 (Task 2 commit - comprehensive Phase 3 tests)

All claims verified:
- context.md contains "Citation Tracking" section ✓
- context.md mentions "generate_source_report" 2 times ✓
- context.md mentions "model_card_id" 1 time ✓
- context.md mentions "DIRECT" 2 times ✓
- context.md mentions "NOT FOUND" 2 times ✓
- Existing content preserved ("Do not interview the user", "Compliance Officer") ✓
- All 23 PDF generator tests pass (12 existing + 11 new) ✓
- All 54 total tests pass ✓

---
*Phase: 03-citation-features-workflow*
*Completed: 2026-02-15*
