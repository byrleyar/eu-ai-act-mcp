---
phase: 12-automated-audit-workflow
plan: "01"
subsystem: testing
tags: [anthropic, pydantic, audit, llm, compliance, scoring]

# Dependency graph
requires:
  - phase: 11-batch-processing-engine
    provides: ProcessingContext, batch artifacts (model_card.txt per model), ComplianceService pattern
provides:
  - AuditService class with audit_model() method
  - FieldAudit/AuditSummary/AuditResult Pydantic models
  - AUDIT_SYSTEM_PROMPT with 1/1i/2/3/4 skeptical auditor rubric
  - build_audit_user_prompt() for dynamic question injection
  - compliance_data.json and audit_results.json persistence
  - 11 unit tests for non-LLM audit logic
affects:
  - 12-02 (next plan in phase -- will call AuditService.audit_model())
  - batch_processor.py (may call AuditService after Phase 12 is complete)

# Tech tracking
tech-stack:
  added: [anthropic SDK]
  patterns:
    - Pydantic Literal types for constrained score values (ScoreValue, ConfidenceValue)
    - Optional client injection pattern for testability (AuditService.__init__ accepts anthropic_client=None)
    - JSON fence stripping for LLM response robustness
    - collections.Counter for score distribution math

key-files:
  created:
    - audit_service.py
    - tests/test_audit_service.py
  modified:
    - requirements.txt

key-decisions:
  - "ScoreValue as Literal string (not int): '1i' cannot be represented as an integer, so all scores are strings"
  - "Optional client injection: AuditService accepts anthropic_client=None for testability without mocking env vars"
  - "JSON fence stripping: LLMs frequently wrap JSON in markdown code fences; strip robustly before json.loads()"
  - "AUDIT_SYSTEM_PROMPT instructs model to return raw JSON array (no markdown fences) but code defensively handles fences anyway"

patterns-established:
  - "Skeptical Auditor Pattern: system prompt explicitly instructs LLM to assume hallucinations may have occurred and requires direct quotes for score 1"
  - "Count-validation after parse: assert len(field_audits) == len(questions) to catch LLM skipping/duplicating entries early"

# Metrics
duration: 8min
completed: 2026-03-02
---

# Phase 12 Plan 01: AuditService Core Summary

**AuditService scoring engine with Pydantic models (FieldAudit/AuditSummary/AuditResult), Skeptical Auditor LLM prompt with 1/1i/2/3/4 rubric, and audit_model() that persists compliance_data.json + audit_results.json**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-02T16:46:30Z
- **Completed:** 2026-03-02T16:54:30Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Created `audit_service.py` with AuditService class, all Pydantic models, AUDIT_SYSTEM_PROMPT with full 1/1i/2/3/4 rubric, and `build_audit_user_prompt()` for dynamic question injection
- Implemented `audit_model()` that reads model_card.txt, calls Anthropic API, validates JSON response count, builds score distribution via Counter, and persists both `compliance_data.json` and `audit_results.json`
- Created `tests/test_audit_service.py` with 11 unit tests covering all non-LLM logic (no Anthropic API calls in tests)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create AuditService with Pydantic models and LLM audit logic** - `6946e55` (feat)
2. **Task 2: Unit tests for audit models, validation, and summary math** - `1aeb341` (test)

**Plan metadata:** (next commit — docs)

## Files Created/Modified

- `/Users/andrew/Code/ai_act_compliance_mcp_server/audit_service.py` - AuditService class, Pydantic models, AUDIT_SYSTEM_PROMPT, build_audit_user_prompt
- `/Users/andrew/Code/ai_act_compliance_mcp_server/tests/test_audit_service.py` - 11 unit tests for non-LLM audit logic
- `/Users/andrew/Code/ai_act_compliance_mcp_server/requirements.txt` - Added `anthropic` SDK dependency

## Decisions Made

- **ScoreValue as Literal string:** `"1i"` cannot be represented as an integer, so all 5 score values are strings — `Literal["1", "1i", "2", "3", "4"]`
- **Optional client injection:** `AuditService.__init__` accepts `anthropic_client=None` so tests can pass a mock without needing env vars or API keys
- **JSON fence stripping:** LLMs frequently wrap output in markdown code fences despite being told not to; the parser defensively strips `\`\`\`json` and `\`\`\`` before `json.loads()`
- **Count-validation:** After parsing, `len(field_audits) == len(questions)` is asserted to catch LLM skipping or duplicating entries early rather than silently producing wrong results

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed anthropic SDK (not yet in venv)**

- **Found during:** Task 1 verification
- **Issue:** `import anthropic` raised `ModuleNotFoundError` because the package was in requirements.txt candidate but not installed
- **Fix:** Ran `pip install anthropic`
- **Files modified:** None (runtime environment only)
- **Verification:** `python3 -c "from audit_service import AuditService"` succeeds
- **Committed in:** N/A (environment install, not a file change)

---

**Total deviations:** 1 auto-fixed (Rule 3 - blocking)
**Impact on plan:** Necessary for local verification. requirements.txt already declared the dependency; this was just runtime environment setup.

## Issues Encountered

None — all Pydantic models, prompt construction, and test assertions worked correctly on first run.

## User Setup Required

The `anthropic` SDK requires an `ANTHROPIC_API_KEY` environment variable at runtime. This is only needed when `AuditService.audit_model()` is called (i.e., in integration/production use). The unit tests in `tests/test_audit_service.py` do NOT call the API and do NOT require the key.

To set the key:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

## Next Phase Readiness

- `AuditService` is importable and ready for integration with the batch processor or a CLI runner (Phase 12 Plan 02)
- `ProcessingContext` from `compliance_service.py` is the expected input — same pattern as Phase 11
- All models are Pydantic v2; `model_dump()` output is JSON-serializable
- 11 tests pass cleanly; adding integration tests that mock `self.client` would complete test coverage

## Self-Check: PASSED

- FOUND: audit_service.py
- FOUND: tests/test_audit_service.py
- FOUND: 12-01-SUMMARY.md
- FOUND: commit 6946e55 (feat - Task 1)
- FOUND: commit 1aeb341 (test - Task 2)
- FOUND: commit 0ff270b (docs - metadata)
- 11 tests pass via `python3 -m pytest tests/test_audit_service.py -v`

---
*Phase: 12-automated-audit-workflow*
*Completed: 2026-03-02*
