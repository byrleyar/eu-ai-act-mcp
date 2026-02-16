# Phase 05 Plan 01 Verification

## Automated Tests
- [ ] `pytest tests/test_coverage_enforcement.py`
- [ ] `pytest tests/test_citation_schema.py`
- [ ] `pytest tests/test_pdf_generator.py`

## Manual Verification

### 1. Missing Questions
**Action**: Call `generate_source_report` with only 5 questions.
**Expected**: Returns an error message listing the ~75 missing question IDs.

### 2. Full Coverage
**Action**: Call `generate_source_report` with a JSON containing all 80+ question IDs.
**Expected**: Returns a success message with a download link and PDF resource.

### 3. Invalid IDs
**Action**: Call `generate_source_report` with a valid ID but also an extra invalid ID.
**Expected**: Succeeds (coverage is met) unless Pydantic validation (Task 1) fails on something else.

## Coverage Checklist
- [ ] `validate_report_coverage` correctly identifies missing IDs.
- [ ] `server.py` correctly loads `questions.json` for validation.
- [ ] Error messages are helpful for LLM retries.
