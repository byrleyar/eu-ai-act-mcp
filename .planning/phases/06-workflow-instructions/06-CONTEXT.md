# Phase 06 Context: Workflow & Instructions

## Decisions & Guardrails

### 1. Just-in-Time Enforcement
- **Dual Enforcement**: Workflow instructions will exist in both `context.md` (long-term memory) and `server.py` tool outputs (active trigger).
- **Mandatory Sequence**: `generate_compliance_doc` must return a system instruction that treats `generate_source_report` as a required next step, not an option.

### 2. Organization & Scannability
- **Categorized Reference**: The list of 80+ question IDs in `context.md` will be categorized by domain (e.g., General, Data, Technical) to help the LLM maintain focus.
- **Full Coverage Requirement**: Claude is strictly required to provide exactly one citation entry per ID, using `NOT FOUND` for any gaps.

### 3. Verification & Transparency
- **Self-Check Protocol**: Claude must re-verify its own DOCX answers against the source text before generating the report.
- **Hallucination Flagging**: Unsupported claims must be flagged as `HALLUCINATED` in the report.

## Deferred Ideas
- (None)
