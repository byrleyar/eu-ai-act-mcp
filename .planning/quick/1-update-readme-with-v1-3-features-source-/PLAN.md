# Quick Task 1: Update README with v1.3 Features

**Goal**: Update `README.md` to reflect the current capabilities of the EU AI Act Compliance MCP Server (v1.3).

## Proposed Changes

### 1. `README.md`
- **Features Section**: 
    - Add **Source Citation Reports (PDF)**: Auditable proof for every answer.
    - Add **Hallucination Detection**: Automated self-checks with bold visual warnings for unsupported claims.
    - Update **Deep Link Analysis**: Mention discovery checklists and agentic retrieval.
- **How It Works Section**:
    - Update to describe the **Agentic Retrieval Loop**: Discovery -> Gap Analysis -> Targeted Fetch -> Generation.
    - Mention the two-document output (DOCX + PDF).
- **Tool List (Files Section)**:
    - Mention `citation_schema.py` and `pdf_generator.py` if appropriate, or just focus on the core server functionality.

## Implementation Steps

### Task 1: Update README.md
1. Refactor "Features" to include PDF reports and Hallucination detection.
2. Refactor "How It Works" to describe the agentic loop.
3. Ensure the Railway deployment instructions are still accurate (specifically the volumes for PDFs).

## Success Criteria
- [ ] README accurately reflects v1.3 capabilities.
- [ ] No broken links or obsolete instructions.
