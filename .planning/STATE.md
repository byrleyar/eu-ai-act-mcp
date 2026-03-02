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
**Phase:** 12 (Automated Audit Workflow) -- in progress
**Plan:** 01 -- complete
**Status:** Phase 12 Plan 01 complete (AuditService core)
**Last activity:** 2026-03-02 — Phase 12 Plan 01 complete

Progress: [▓▓▓▓░░░░░░] 40% (v1.4)

## Performance Metrics

**v1.4 Milestone (in progress):**
- Phases: 1 of 3 complete (Phase 11 done; Phase 12 in progress)
- Plans: 2 of N complete
- Requirements: 7 of 14 complete

| Phase | Plan | Duration | Tasks | Files | Tests | Status   |
|-------|------|----------|-------|-------|-------|----------|
| 11    | 01   | 10min    | 5     | 7     | 5     | Complete |
| 12    | 01   | 8min     | 2     | 3     | 11    | Complete |

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

See .planning/PROJECT.md Key Decisions table for full history.

### Roadmap Evolution

- Phase 10 added: Fix Source Report Layout and Document Attribution

### Active TODOs

- Milestone v1.4 in progress. Phase 12 Plan 01 complete. Next: Phase 12 Plan 02 (audit CLI/runner integration).

### Known Blockers

None.

## Session Continuity

**Summary:**
- v1.3 is fully shipped.
- v1.4 in progress: Automated Batch Testing & Compliance Audit.
- Phase 11 complete: batch CLI fetches model cards + saves artifacts per model.
- Phase 12 Plan 01 complete: AuditService core built (Pydantic models, LLM prompt, audit_model() method, 11 unit tests).
- Input: CSV/List of models.
- Output: Compliance docs + Audit reports with performance scores.

---

## Last Session

**Timestamp:** 2026-03-02
**Stopped at:** Completed Phase 12 Plan 01 (AuditService core). 2 tasks committed atomically. SUMMARY.md created.
**Next action:** Phase 12 Plan 02 -- integrate AuditService into batch workflow or CLI runner.

---

*State tracking for: EU AI Act Compliance MCP Server*
*Created: 2026-02-15*
*Last updated: 2026-03-02 after completing Phase 12 Plan 01*
