# Project State

**Project:** EU AI Act Compliance MCP Server
**Status:** Milestone v1.5 — ARCHIVED (2026-03-03)
**Last Updated:** 2026-03-03

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-03)

**Core value:** Every answer in the compliance document must be traceable back to its source.
**Current focus:** v1.5 archived. Planning next milestone.

## Current Position

**Milestone:** v1.5 (Analytical Reporting) — COMPLETE & ARCHIVED
**Last Completed Phase:** 15-batch-report-generator (2/2 plans done)
**Status:** All phases archived. Ready for next milestone planning.

## Performance Metrics

**v1.4 Milestone (complete):**
- Phases: 4 of 4 complete (Phase 11 done; Phase 12 done; Phase 13 done; Phase 14 done)
- Plans: 7 of 7 complete
- Requirements: 14 of 14 complete (+ 4 tech debt items closed)

| Phase | Plan | Duration | Tasks | Files | Tests | Status   |
|-------|------|----------|-------|-------|-------|----------|
| 11    | 01   | 10min    | 5     | 7     | 5     | Complete |
| 12    | 01   | 8min     | 2     | 3     | 11    | Complete |
| 12    | 02   | ~45min   | 2     | 2     | 3     | Complete |
| 13    | 01   | 3min     | 2     | 3     | 11    | Complete |
| 13    | 02   | ~5min    | 3     | 2     | 4     | Complete |
| 14    | 01   | 2min     | 2     | 4     | 0     | Complete |

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

**v1.5 Milestone (complete):**
- Phases: 1 of 1 complete (Phase 15 done)
- Plans: 2 of 2 complete

| Phase | Plan | Duration | Tasks | Files | Tests | Status   |
|-------|------|----------|-------|-------|-------|----------|
| 15    | 01   | 3min     | 2     | 1     | 0     | Complete |
| 15    | 02   | 4min     | 2     | 1     | 0     | Complete |

## Quick Tasks Completed

| # | Task | Files | Date |
|---|------|-------|------|
| 1 | Update README with v1.3 features | 1 | 2026-02-16 |
| 2 | Switch AuditService to claude-opus-4-6 with extended thinking | 1 | 2026-03-03 |
| 3 | Add verify_model_cards.py to check HF model cards from CSV | 1 | 2026-03-03 |
| 4 | Split audit_model() into Sonnet form-fill + Opus scoring steps | 1 | 2026-03-03 |

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
- **Repeat section name in Sheet1 rows (vs. cell merge)**: Keeps data filterable and sortable in Excel without breaking cell references.
- **executive_summary.txt fixed-width padding**: Labels left-justified to ~20 chars using f-string padding for clean terminal/text-viewer alignment.

**Phase 14:**
- **No architectural changes needed**: All four tech debt items were in-place fixes (test assertions, import removal, path portability, doc creation) — no new tables, services, or dependencies introduced.
- **Planning files untracked by git**: 13-VERIFICATION.md and 14-01-SUMMARY.md exist on disk but are not committed (by design since commit 8ae427c).

**Phase 15:**
- **SECTION_MAP single source of truth**: generate_report.py imports SECTION_MAP from report_generator (not redefined) — SECTION_MAP_INVERTED built from it at module level.
- **domain column (not use_case)**: combined_field_audits.csv and table4 use `domain` matching actual test_models.csv column name.
- **fmt_mean_sd() SD gating**: SD shown in parentheses only when n > 2, avoiding misleading precision for small groups.
- **pandas select_dtypes forward-compat**: Uses `["object", "string"]` not `"object"` alone to silence pandas 3 deprecation.
- **question_problem_table (df, has_data) tuple**: Explicit bool for empty-data guard; caller renders blockquote fallback if has_data=False.
- **make_table6 (df, footnote) tuple**: Footnote kept out of DataFrame so raw CSV export has no "*" markers.
- **Commentary from actual output values**: Commentary functions read formatted DataFrames to surface real names/numbers (not placeholder text).
- **datetime.now(tz=timezone.utc)**: Forward-compatible replacement for deprecated datetime.utcnow().

See .planning/PROJECT.md Key Decisions table for full history.

### Roadmap Evolution

- Phase 10 added: Fix Source Report Layout and Document Attribution
- Phase 15 added: Batch Report Generator (v1.5 Analytical Reporting milestone)

### Active TODOs

None. Milestone v1.5 complete and archived.

### Known Blockers

None.

## Session Continuity

**Summary:**
- v1.5 is fully shipped and archived: Analytical Reporting complete.
- Full batch pipeline: batch_processor → audit_processor → report_generator → generate_report
- Output: Compliance DOCX/PDF + audit_results.json + batch_report.xlsx + batch_report.md (8 tables + commentary) + 9 CSVs

---

## Last Session

**Timestamp:** 2026-03-03T19:00:00Z
**Stopped at:** v1.5 milestone archived — MILESTONES.md updated, ROADMAP.md reorganized, PROJECT.md evolved, STATE.md updated, git tag v1.5 created.
**Next action:** `/gsd:new-milestone` — start v1.6 planning.

---

*State tracking for: EU AI Act Compliance MCP Server*
*Created: 2026-02-15*
*Last updated: 2026-03-03 after v1.5 milestone archived*
