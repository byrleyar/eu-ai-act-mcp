# Phase 06 Research: Workflow & Instructions

## Objective
Overhaul `context.md` to ensure Claude reliably executes the compliance workflow, detects hallucinations, and maintains full coverage across 80+ questions.

## Key Requirements Analysis

### 1. Self-Verification & Hallucination Detection (HALL-03)
Claude must be instructed to critically evaluate its own answers. 
- **Action**: Add a "Self-Verification Protocol" section to `context.md`.
- **Instruction**: "Before generating citations, compare each answer in your compliance document draft against the model card. If you cannot find any supporting evidence (direct or inferred), mark it as `HALLUCINATED`."

### 2. Full Coverage (COV-03, COV-04)
Claude needs to know the exact set of IDs to include in the source report to satisfy the new server-side validation.
- **Action**: Embed the full list of question IDs in `context.md` or provide a clear instruction to always include every ID from `questions.json`.
- **Instruction**: "Your source report MUST contain exactly one citation entry for every question ID listed in `questions.json`. For questions where no information was found, use the `NOT FOUND` confidence level and explain where you searched."

### 3. Tool Sequencing & Link Presentation (WORK-01, WORK-02)
The v1.1 experience often resulted in Claude only calling the first tool or presenting links separately.
- **Action**: Define a strict "Final Response Protocol".
- **Instruction**: "1. Call `generate_compliance_doc`. 2. Call `generate_source_report`. 3. ONLY after both tools have returned, present BOTH download links to the user in a single cohesive response."

## Proposed `context.md` Structure

### Section 1: Core Automation & ID Requirement
(Preserve v1.1 focus on specific HF IDs and best-effort automation)

### Section 2: The Two-Step Compliance Workflow
Explicitly define the sequence:
1. `fetch_hf_model_card`
2. `get_compliance_requirements`
3. Internal Draft & Self-Verification
4. `generate_compliance_doc`
5. `generate_source_report`

### Section 3: Citation & Verification Protocol
- Detailed definitions of confidence levels (including `HALLUCINATED`).
- Strict rule on 100% question coverage.
- Formatting rules for the JSON.

### Section 4: Question ID Reference
A compact list of all ~80 question IDs to serve as a checklist for the LLM.

## Risks & Mitigations
- **Context Window**: Adding 80 IDs might eat some tokens, but it's necessary for 100% coverage reliability.
- **Compliance Fatigue**: If the instructions are too long, Claude might skip some. Keep it punchy and use bold/caps for critical rules.

## Verification Plan
- Manual test with a real model card to see if Claude:
    - Calls both tools.
    - Includes all IDs.
    - Presents both links together.
    - Correctely identifies a (simulated) hallucination.
