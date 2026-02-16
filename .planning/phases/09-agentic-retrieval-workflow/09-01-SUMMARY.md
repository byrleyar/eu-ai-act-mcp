---
phase: 09-agentic-retrieval-workflow
plan: 01
subsystem: workflow-instructions
tags:
  - agentic-workflow
  - gap-analysis
  - targeted-fetch
dependency_graph:
  requires:
    - context.md
    - server.py (fetch_external_document tool)
  provides:
    - Discovery -> Gap Analysis -> Fetch loop instructions
    - Context budgeting guidelines
    - Retrieval relevance instructions
  affects:
    - context.md (complete replacement)
tech_stack:
  added: []
  patterns:
    - Agentic loop pattern (Discover, Plan, Act, Finalize)
    - Context conservation strategy
key_files:
  created: []
  modified:
    - context.md
decisions:
  - Shifted compliance persona from "passive form-filler" to "active investigator".
  - Explicitly instructed Claude to fetch missing data before answering.
  - Retained strict coverage and hallucination rules from v1.2 as the "safety net" for this new autonomous behavior.
metrics:
  duration_seconds: 120
  tasks_completed: 3
  files_modified: 1
  files_created: 0
  tests_passing: 77
  completed: 2026-02-16
---

# Phase 09 Plan 01: Agentic Retrieval Workflow Summary

**One-liner:** Overhauled `context.md` to instruct Claude to actively discover, analyze gaps, and fetch external documents to fill missing compliance data, transforming the system from a simple form-filler to an agentic investigator.

## Objective Achieved

The system instructions now define a sophisticated **Agentic Retrieval Loop**. Instead of guessing or marking "N/A" when the model card is sparse, Claude is explicitly guided to:
1.  **Discover**: See the menu of available technical reports.
2.  **Analyze Gaps**: Compare what it has vs. what it needs.
3.  **Fetch**: Selectively retrieve only the documents that fill those gaps.
4.  **Synthesize**: Combine all sources into a high-fidelity report.

## Tasks Completed

### Task 1 & 2: Overhaul `context.md`
**Status:** Complete
Replaced the previous instructions with the new agentic workflow. The document now clearly outlines the 5-step loop (Discovery, Requirement Alignment, Gap Analysis, Targeted Fetch, Consolidated Generation) and includes specific principles for judging link relevance and budgeting context.

### Task 3: Verification
**Status:** Complete
Verified that the ID checklist is intact, the new `fetch_external_document` tool is integrated into the flow, and the "Just-in-Time" enforcement rules from Phase 6 are preserved as the final safety barrier.

## Success Criteria

- [x] `context.md` instructs Claude to fetch missing docs before answering.
- [x] The workflow sequence is updated to include the fetch tool.
- [x] All 80+ question IDs are still present and categorized.
- [x] Instructions for context efficiency (budgeting) are included.

## Self-Check: PASSED

**Modified files exist:**
```
FOUND: /Users/andrew/Antigravity/ai_act_compliance_mcp_server/context.md
```

**All claims verified.**
