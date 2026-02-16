# Phase 09 Plan 01 Verification

## Manual Checklist

### 1. Content Verification
- [ ] `fetch_external_document` is part of the core workflow steps.
- [ ] "Gap Analysis" is defined as a requirement before generation.
- [ ] The categorized question ID list is present and matches `questions.json`.
- [ ] Instructions for choosing which links to fetch are clear.
- [ ] Self-verification protocol is preserved.

### 2. Execution Roleplay (Simulated)
**Scenario**: Model card lists a "Technical Report" PDF but doesn't mention "Energy Usage" in the card text.
**Expected Claude Behavior (per new instructions)**:
1. Fetches model card.
2. Sees "Technical Report" in discovered links.
3. Analyzes requirements, sees Energy Usage is missing.
4. Judges "Technical Report" as likely containing energy info.
5. Calls `fetch_external_document` for the PDF.
6. Answers Energy Usage based on the PDF.
7. Calls document generation tools.

## Retrieval Workflow Checklist
- [ ] Promotes proactive investigation.
- [ ] Prevents context bloat (fetch only what is needed).
- [ ] Explicitly links Discovery -> Gaps -> Fetch.
