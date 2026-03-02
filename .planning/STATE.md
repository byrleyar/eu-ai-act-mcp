# Project State

**Project:** EU AI Act Compliance MCP Server
**Status:** Milestone v1.4 -- in progress
**Last Updated:** 2026-03-02

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-02)

**Core value:** Every answer in the compliance document must be traceable back to its source.
**Current focus:** Milestone v1.4 -- Automated Batch Testing & Compliance Audit.

## Current Position

**Milestone:** v1.4 (Automated Batch Testing & Compliance Audit)
**Phase:** 13 (Aggregate Results & Reporting) -- in progress
**Plan:** 01 -- complete
**Status:** Phase 13 Plan 01 complete (ReportGenerator core, CSV, 11 tests). Next: Phase 13 Plan 02 (Excel workbook)
**Last activity:** 2026-03-02 — Phase 13 Plan 01 complete (ReportGenerator, SECTION_MAP, compute_metrics, batch_report.csv)

Progress: [▓▓▓▓▓▓░░░░] 60% (v1.4)

## Performance Metrics

**v1.4 Milestone (in progress):**
- Phases: 2 of 3 complete (Phase 11 done; Phase 12 done; Phase 13 in progress)
- Plans: 4 of N complete
- Requirements: 10 of 14 complete

| Phase | Plan | Duration | Tasks | Files | Tests | Status   |
|-------|------|----------|-------|-------|-------|----------|
| 11    | 01   | 10min    | 5     | 7     | 5     | Complete |
| 12    | 01   | 8min     | 2     | 3     | 11    | Complete |
| 12    | 02   | ~45min   | 2     | 2     | 3     | Complete |
| 13    | 01   | 3min     | 2     | 3     | 11    | Complete |

**v1.3 Milestone (complete):**
- Phases: 3 of 3 complete
- Plans: 3 of 3 complete
- Requirements: 8 of 8 complete (ACQ)

| Phase | Plan | Duration | Tasks | Files | Tests | Status   |
|-------|------|----------|-------|-------|-------|----------|
| 07    | 01   | 240s     | 4     | 2     | 5     | Complete |
| 08    | 01   | 300s     | 3     | 1     | 5     | Complete |
| 09    | 01   | 120s     | 3     | 1     | 0     | Complete |

**Post-v1.3 Fixes:**
- Phase 10 (Fix Source Report Layout): 1 of 1 complete

| Phase | Plan | Duration | Tasks | Files | Tests | Status   |
|-------|------|----------|-------|-------|-------|----------|
| 10    | 01   | 98s      | 3     | 2     | 3     | Complete |

## Quick Tasks Completed

| # | Task | Files | Date |
|---|------|-------|------|
| 1 | Update README with v1.3 features | 1 | 2026-02-16 |

**v1.2 Milestone (archived):**
- Phases: 3, Plans: 3, Requirements: 10/10
- See .planning/milestones/v1.2-ROADMAP.md

**v1.1 Milestone (archived):**
- Phases: 3, Plans: 8, Requirements: 25/25
- See .planning/milestones/v1.1-REQUIREMENTS.md

## Accumulated Context

### Key Decisions Made

**Phase 7:**
- **Agentic Choice**: Disabled automatic fetch in `fetch_hf_model_card` to empower the LLM to choose sources.

**Phase 8:**
- **SSRF Protection**: Strict validation of external URLs to block private IP ranges.
- **Optimized PDF Extraction**: Limited to first 15 pages for context efficiency.

**Phase 9:**
- **Investigator Workflow**: Shifted instructions to a "Discovery -> Gaps -> Fetch" loop.

**Phase 10:**
- **Column Width Selection**: Section column set to 0.8" (not 0.75") based on research showing minimum width for 9pt DejaVu Sans.
- **Document Attribution Consistency**: Extended INFERRED citations to show document and section attribution, matching DIRECT citation format.

**Phase 11:**
- **ComplianceService Pattern**: Extracted all core logic from server.py into ComplianceService class, reused by both MCP server and batch CLI.
- **ProcessingContext State Isolation**: Fresh ProcessingContext per model iteration to prevent state leakage (BAT-03).
- **Batch Artifacts Design**: Save model_card.txt + discovered_links.json + compliance_data_template.json per model; full automated analysis deferred to Phase 12.

**Phase 12:**
- **ScoreValue as Literal string**: "1i" cannot be represented as an integer, so all 5 score values are strings -- Literal["1", "1i", "2", "3", "4"].
- **Optional client injection**: AuditService accepts anthropic_client=None for testability without mocking env vars.
- **JSON fence stripping**: LLMs frequently wrap output in markdown code fences; the parser defensively strips fences before json.loads().
- **Count-validation**: After parsing, assert len(field_audits) == len(questions) to catch LLM skipping/duplicating entries early.
- **Typer single-command app**: @app.command() registers function as default command; invocation is `python audit_processor.py batches/...` (no `run` subcommand needed).
- **ProcessingContext reused**: AuditService receives ProcessingContext with output_path=str(model_dir) to route outputs into model subdirectory.
- **model_id recovery**: Directory name `__` separator reversed to `/` via simple string replace, matching inverse of sanitize_model_id.

**Phase 13:**
- **score_counts stored in model dict**: discover_audited_models stores remapped score_counts alongside metrics so write_csv can access raw counts without re-reading files.
- **Startup assertion at module level**: SECTION_MAP drift caught at import time via assertion against questions.json.
- **openpyxl declared in Plan 01**: Even though xlsx generation is Plan 02, dependency declared now so Plan 02 import works cleanly.

See .planning/PROJECT.md Key Decisions table for full history.

### Roadmap Evolution

- Phase 10 added: Fix Source Report Layout and Document Attribution

### Active TODOs

- Milestone v1.4 in progress. Phase 12 complete. Phase 13 in progress (Plan 01 done). Next: Phase 13 Plan 02 (Excel workbook generation).

### Known Blockers

None.

## Session Continuity

**Summary:**
- v1.3 is fully shipped.
- v1.4 in progress: Automated Batch Testing & Compliance Audit.
- Phase 11 complete: batch CLI fetches model cards + saves artifacts per model.
- Phase 12 complete: AuditService core (12-01) + audit_processor.py CLI (12-02). End-to-end validated: 80 field_audits with non-trivial score distribution for facebook/opt-125m. 102 tests passing.
- Phase 13 Plan 01 complete: ReportGenerator core -- SECTION_MAP (8 sections, 80 questions), compute_metrics, load_audit_results, discover_audited_models with score key remapping, write_csv, batch_report.csv, Typer CLI. 11 unit tests passing. 113 tests total.
- Input: CSV/List of models.
- Output: Compliance docs + Audit reports with performance scores + batch_report.csv/xlsx.

---

## Last Session

**Timestamp:** 2026-03-02
**Stopped at:** Completed Phase 13 Plan 01 (ReportGenerator core, SECTION_MAP, compute_metrics, batch_report.csv). 2 tasks complete. SUMMARY.md created. 11 unit tests passing.
**Next action:** Phase 13 Plan 02 -- Excel workbook generation (batch_report.xlsx, 3 sheets).

---

*State tracking for: EU AI Act Compliance MCP Server*
*Created: 2026-02-15*
*Last updated: 2026-03-02 after completing Phase 13 Plan 01*
