# Phase 05 Research: Coverage Enforcement

## Objective
Ensure the `generate_source_report` tool rejects citation JSON that does not cover every question defined in `questions.json`.

## Current Implementation
- `server.py` defines `generate_source_report(source_citations_json: str, ...)`
- It calls `validate_citation_json(source_citations_json)` from `citation_schema.py`.
- `citation_schema.py` uses Pydantic to validate that the JSON structure matches `CitationReport`.
- `CitationReport` requires at least one citation (`min_length=1`) but does not know about `questions.json`.
- `questions.json` contains ~80 questions.

## Proposed Strategy

### 1. Authoritative Question Source
`questions.json` is the source of truth. The validation logic must load this file to get the list of required IDs.

### 2. Validation Logic Location
Options:
- **A. Inside `citation_schema.py`**: Add a function `validate_coverage(report, questions_path)` or update `validate_citation_json` to take an optional `required_ids` list.
- **B. Inside `server.py`**: Add the coverage check directly in the tool implementation.

**Decision:** Option A (inside `citation_schema.py`). Keeping validation logic near the schema definition is cleaner and more testable. `validate_citation_json` should be updated to optionally enforce coverage if `required_ids` are provided, or a new function `validate_report_coverage(report, required_ids)` should be added.

### 3. Error Reporting
If questions are missing, the error message must list the specific missing IDs to help the LLM fix the input.

Example error:
`Validation Error: Missing citations for 3 questions: [legal_name, model_name, release_date]`

### 4. Integration in `server.py`
The `generate_source_report` tool in `server.py` will:
1. Load `questions.json`.
2. Extract the list of IDs.
3. Call the updated validation logic.
4. Catch the `ValueError` (or custom exception) and return it as a string to the user.

## Technical Details
- `questions.json` structure: `[{"id": "...", "question": "...", "description": "..."}, ...]`
- Extraction: `required_ids = [q['id'] for q in questions]`
- Comparison: `missing = set(required_ids) - set(c.question_id for c in report.citations)`

## Risks & Mitigations
- **Performance**: Loading `questions.json` on every call is cheap (~80 small objects).
- **Strictness**: LLMs might forget 1-2 questions. Clear error messages are essential for them to retry.
- **Synchronicity**: If `questions.json` changes, the validator automatically picks it up.

## Verification Plan
- Unit test for `validate_report_coverage` with complete and incomplete citation lists.
- Integration test for `generate_source_report` tool (mocking file I/O if necessary).
- Manual verification via MCP tool call with a subset of questions.
