# Phase 09 Research: Agentic Retrieval Workflow

## Objective
Overhaul `context.md` to guide Claude through a targeted retrieval loop, ensuring it discovers, analyzes gaps, and fetches external documentation to fill them before generating compliance reports.

## The New Retrieval Loop

### 1. Discovery & Checklist
- **Tool**: `fetch_hf_model_card`
- **Output**: Model card text + `### DISCOVERED DOCUMENTS` JSON array.
- **Goal**: LLM sees a "menu" of potential sources early.

### 2. Requirement Alignment
- **Tool**: `get_compliance_requirements`
- **Output**: All 80+ question IDs.
- **Goal**: LLM establishes the "target state" (what needs to be answered).

### 3. Gap Analysis (Internal Reasoning)
- **Instruction**: "Compare the Model Card text against the 80 requirements. Identify specific sections where data is missing (e.g., 'Training Compute', 'Energy Consumption')."
- **Goal**: LLM identifies exactly what it doesn't know.

### 4. Targeted Retrieval (Iterative)
- **Tool**: `fetch_external_document`
- **Instruction**: "If a discovered link's title or context suggests it contains missing info, fetch it. Fetch only what is necessary to fill identified gaps."
- **Goal**: Proactive data acquisition without context bloat.

### 5. Consolidated Generation
- **Tools**: `generate_compliance_doc` -> `generate_source_report`.
- **Goal**: Use all gathered sources (Model Card + fetched docs) for high-fidelity answers.

## Context Budgeting & Efficiency
- **Problem**: Fetching multiple 15-page PDFs might hit token limits.
- **Strategy**:
    - "Only fetch docs that clearly target your gaps."
    - "If you fetch multiple docs, summarize the first before fetching the second if context is tight."
    - "Prioritize primary technical reports over secondary blog posts or demo links."

## Instruction Tone
- Move from "Best effort" to "Proactive investigator".
- Stress that a `NOT FOUND` answer is only acceptable after checking relevant discovered documents.

## Verification Plan
- Manual verification of the `context.md` file.
- Roleplay as the LLM to ensure the instructions are not contradictory or too verbose.
