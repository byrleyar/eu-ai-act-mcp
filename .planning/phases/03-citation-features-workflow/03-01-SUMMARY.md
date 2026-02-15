---
phase: 03-citation-features-workflow
plan: 01
subsystem: pdf-generation
tags: [reportlab, pdf, visual-formatting, audit-reports, confidence-coloring]

# Dependency graph
requires:
  - phase: 02-mcp-tool-integration
    provides: Basic PDF generation infrastructure with DejaVu Sans font, validation, and MCP tool
provides:
  - Enhanced PDF generator with executive summary showing confidence breakdown
  - WCAG AA compliant confidence-based row coloring (DIRECT/INFERRED/DEFAULT/NOT FOUND)
  - Hierarchical citation display with italicized quotes and formatted reasoning
  - Page footer with model card ID and generation timestamp
  - model_card_id parameter support in MCP tool
affects: [03-02, audit-workflow, citation-features]

# Tech tracking
tech-stack:
  added: [collections.Counter for confidence tallying]
  patterns: [Factory function pattern for footer callbacks, confidence-based conditional formatting]

key-files:
  created: []
  modified: [pdf_generator.py, server.py]

key-decisions:
  - "Use WCAG AA compliant colors (#D4EDDA, #FFF3CD, #E7E8EA, #F8D7DA) for confidence levels ensuring 4.5:1+ contrast"
  - "Format citation content differently per confidence type: DIRECT shows italicized quotes, INFERRED shows reasoning chain, DEFAULT explains rationale, NOT FOUND documents search attempts"
  - "Use question_id in first column instead of sequential numbering for cross-referencing with questions.json"
  - "Increase bottom margin from 0.5 to 0.75 inch to accommodate footer without overlap"

patterns-established:
  - "Footer callback factory pattern: _create_footer_callback(params) returns closure for doc.build()"
  - "Confidence-based conditional formatting: Switch on confidence level to determine cell content structure"
  - "Executive summary builder: Separate helper function returns list of flowables for modular story construction"

# Metrics
duration: 3min
completed: 2026-02-15
---

# Phase 03 Plan 01: Enhanced PDF Citation Report with Visual Formatting

**Executive summary with confidence breakdown, WCAG AA color-coded citation rows, hierarchical display per confidence type, and audit-ready page footers**

## Performance

- **Duration:** 3 minutes
- **Started:** 2026-02-15T14:23:33Z
- **Completed:** 2026-02-15T14:26:54Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- PDF reports now include executive summary section showing model card ID, total questions, and confidence breakdown with counts and percentages
- Confidence-based row coloring using WCAG AA compliant colors ensures visual hierarchy for audit trail assessment
- Citation content formatted hierarchically: DIRECT citations show italicized source quotes, INFERRED shows reasoning chain, DEFAULT explains rationale, NOT FOUND documents search attempts
- Page footer displays model card identifier and generation timestamp on every page for audit traceability
- MCP tool accepts optional model_card_id parameter for complete metadata tracking

## Task Commits

Each task was committed atomically:

1. **Task 1: Add confidence colors, citation hierarchy, and executive summary to PDF generator** - `dc79a6b` (feat)
2. **Task 2: Add footer callback and pass model_card_id from server.py** - `082bbf0` (feat)

## Files Created/Modified
- `pdf_generator.py` - Added CONFIDENCE_COLORS constant, _build_executive_summary helper, _create_footer_callback factory, enhanced table formatting with confidence-based coloring, updated function signature to accept model_card_id
- `server.py` - Added model_card_id parameter to generate_source_report tool, passed through to PDF generator

## Decisions Made

**Decision:** Use WCAG AA compliant colors for confidence levels
**Rationale:** Ensures 4.5:1+ contrast ratio with black text for accessibility. Light green (#D4EDDA) for DIRECT, light yellow (#FFF3CD) for INFERRED, light gray (#E7E8EA) for DEFAULT, light red (#F8D7DA) for NOT FOUND provides intuitive color coding that meets accessibility standards.

**Decision:** Format citation Source/Details column content based on confidence type
**Rationale:** Different confidence levels represent fundamentally different citation patterns. DIRECT citations have verbatim quotes worthy of italic emphasis; INFERRED citations need reasoning chain display; DEFAULT citations need rationale explanation; NOT FOUND citations document search attempts. Tailored formatting makes each type immediately recognizable.

**Decision:** Use question_id in first table column instead of row numbers
**Rationale:** Enables cross-referencing between PDF report and questions.json. Auditors can trace specific questions back to schema definition. Maintains stable identifiers across report regenerations.

**Decision:** Increase bottom margin to 0.75 inch for footer
**Rationale:** Default 0.5 inch margin didn't leave sufficient space for footer without overlapping table content. 0.75 inch provides comfortable buffer for 8pt footer text at 0.3 inch from bottom.

## Deviations from Plan

None - plan executed exactly as written. All enhancements implemented per specification with no additional work required.

## Issues Encountered

None - implementation proceeded smoothly. All existing tests passed without modification, confirming backward compatibility. New features integrated cleanly with existing PDF infrastructure.

## User Setup Required

None - no external service configuration required. All changes are internal to PDF generation and MCP tool signature.

## Next Phase Readiness

Ready for Phase 03 Plan 02 (Citation Features Workflow):
- PDF generation infrastructure now supports all visual formatting requirements
- model_card_id parameter plumbed through from MCP tool to PDF footer and summary
- Executive summary provides confidence breakdown for workflow decision-making
- All 43 existing tests pass, confirming no regressions

Foundation complete for user-facing citation workflow features and multi-format export capabilities.

## Self-Check: PASSED

All files and commits verified:
- FOUND: pdf_generator.py
- FOUND: server.py
- FOUND: dc79a6b (Task 1 commit)
- FOUND: 082bbf0 (Task 2 commit)

---
*Phase: 03-citation-features-workflow*
*Completed: 2026-02-15*
