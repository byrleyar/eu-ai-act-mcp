---
phase: 13-aggregate-results-reporting
plan: "01"
subsystem: reporting
tags: [report_generator, csv, openpyxl, typer, rich, SECTION_MAP, metrics]

# Dependency graph
requires:
  - phase: 12-automated-audit-workflow
    provides: audit_results.json per model with score counts and field_audits list

provides:
  - ReportGenerator class with discover_audited_models, write_csv, generate methods
  - SECTION_MAP constant mapping 8 sections to 80 question IDs (validated at import time)
  - compute_metrics() helper computing 6 audit rate metrics from score counts
  - load_audit_results() helper loading audit_results.json with scores_by_qid dict
  - batch_report.csv with per-model score counts and percentage metrics
  - CSV_FIELDNAMES list (model_id, status, total_fields, score_1..4, pct metrics)
  - Typer CLI entry point (report_generator.py batch_dir)
  - openpyxl declared in requirements.txt for Plan 02

affects:
  - 13-02 (Excel workbook generation extends ReportGenerator.generate placeholder)

# Tech tracking
tech-stack:
  added: [openpyxl (requirements.txt, for Plan 02 xlsx generation)]
  patterns:
    - "SECTION_MAP: hardcoded constant with startup assertion against questions.json"
    - "Key remapping: score_1_count -> score_1 before calling compute_metrics"
    - "score_counts dict stored on model dict so write_csv does not need to recompute"

key-files:
  created:
    - report_generator.py
    - tests/test_report_generator.py
  modified:
    - requirements.txt

key-decisions:
  - "score_counts stored in model dict: discover_audited_models stores remapped score_counts alongside metrics so write_csv can access raw counts without re-reading files"
  - "Startup assertion validates SECTION_MAP against questions.json at module import time to catch drift immediately"
  - "openpyxl added to requirements.txt in Plan 01 even though xlsx generation is deferred to Plan 02 -- Plan 02 imports report_generator.py so the dependency needs to be declared now"

patterns-established:
  - "Pattern 1: ReportGenerator.generate() as orchestrator with placeholder stubs for Plan 02 (write_xlsx, write_executive_summary)"
  - "Pattern 2: compute_metrics() accepts plain keys (score_1, score_1i, ...) while audit_results.json uses _count suffix -- remapping is explicit in discover_audited_models"

# Metrics
duration: 3min
completed: 2026-03-02
---

# Phase 13 Plan 01: ReportGenerator Core Summary

**ReportGenerator class with SECTION_MAP (8 sections, 80 questions), score key remapping, compute_metrics(), CSV generation, and Typer CLI -- 11 tests passing**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-02T20:05:16Z
- **Completed:** 2026-03-02T20:07:34Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- ReportGenerator class with discover_audited_models, write_csv, and generate methods
- SECTION_MAP constant hardcoded from hackathon xlsx: 8 sections, 80 question IDs, with startup assertion against questions.json
- score_1_count -> score_1 key remapping explicitly applied in discover_audited_models before calling compute_metrics
- compute_metrics() returning 6 rates: accuracy, hallucination, gap, na, pass, fail
- batch_report.csv written with per-model score counts and 0-100 percentage metrics
- 11 unit tests covering SECTION_MAP completeness, metric computation, CSV format, model discovery, and key remapping

## Task Commits

Each task was committed atomically:

1. **Task 1: Create report_generator.py with ReportGenerator class and Typer CLI** - `dcbee4c` (feat)
2. **Task 2: Unit tests for SECTION_MAP, metrics, CSV, model discovery, and key remapping** - `645de22` (feat)

## Files Created/Modified

- `report_generator.py` - ReportGenerator class, SECTION_MAP constant, compute_metrics/load_audit_results helpers, CSV generation, Typer CLI
- `tests/test_report_generator.py` - 11 unit tests covering all core logic
- `requirements.txt` - openpyxl added for Plan 02 xlsx generation

## Decisions Made

- **score_counts stored in model dict:** `discover_audited_models` stores the remapped `score_counts` dict on each model result dict alongside `metrics`. This lets `write_csv` access both raw counts and computed rates without needing to re-read files or reverse-compute.
- **Startup assertion at module level:** The assertion `_mapped_ids == _expected_ids` runs at import time so any SECTION_MAP drift is caught immediately on server/CLI startup, not silently during report generation.
- **openpyxl in requirements.txt now (Plan 01):** Even though xlsx generation is a Plan 02 task, `report_generator.py` will be imported by Plan 02 code. Declaring the dependency in Plan 01 ensures a clean Plan 02 execution.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- report_generator.py is importable and tested. Plan 02 can extend `ReportGenerator.generate()` by replacing the `pass` placeholder stubs for `write_xlsx` and `write_executive_summary`.
- SECTION_MAP provides the section-to-question-ID mapping Plan 02 needs for Sheet1 (Per-Field Detail) and Sheet2 (Section Summary) layout.
- CSV_FIELDNAMES is exported for any downstream consumers.

## Self-Check

**Files exist:**
- report_generator.py: FOUND
- tests/test_report_generator.py: FOUND
- requirements.txt (contains openpyxl): FOUND

**Commits exist:**
- dcbee4c: FOUND
- 645de22: FOUND

## Self-Check: PASSED

---
*Phase: 13-aggregate-results-reporting*
*Completed: 2026-03-02*
