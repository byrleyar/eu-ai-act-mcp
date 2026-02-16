---
phase: 07-discovery-engine
plan: 01
subsystem: discovery-server
tags:
  - discovery
  - link-extraction
  - huggingface-hub
dependency_graph:
  requires:
    - server.py
    - huggingface_hub
  provides:
    - Structured link discovery checklist
    - Context-aware link extraction
    - BibTeX/ArXiv parsing
    - Repository file listing
  affects:
    - server.py (fetch_hf_model_card refactored)
    - tests/test_link_discovery.py (new tests)
tech_stack:
  added: []
  patterns:
    - Regex-based link extraction with context capture
    - API-based repo file listing
key_files:
  created:
    - tests/test_link_discovery.py
  modified:
    - server.py
decisions:
  - Stopped automatic fetching of external content in `fetch_hf_model_card` to prepare for agentic workflow.
  - Implemented specialized regex for Markdown, HTML, and BibTeX/ArXiv patterns.
  - Included 100 characters of context around each link to help LLM relevance judgment.
metrics:
  duration_seconds: 240
  tasks_completed: 4
  files_modified: 1
  files_created: 1
  tests_added: 5
  tests_passing: 72
  completed: 2026-02-16
---

# Phase 07 Plan 01: Implement Discovery Engine Summary

**One-liner:** Enhanced `fetch_hf_model_card` to proactively discover and list technical documents (papers, repo files, citations) without fetching them, enabling a targeted agentic retrieval workflow.

## Objective Achieved

The `fetch_hf_model_card` tool now returns a structured `### DISCOVERED DOCUMENTS` checklist at the end of its response. This checklist includes:
- **Repository Files**: PDFs found directly in the Hugging Face repo file list.
- **Citations**: arXiv links extracted from BibTeX blocks.
- **Web Links**: Markdown and HTML links found in the model card text.
- **Context**: 100 characters of surrounding text for each link to help the LLM judge relevance.

Crucially, automatic fetching of these links has been **disabled**, paving the way for the new `fetch_external_document` tool in Phase 8.

## Tasks Completed

### Task 1: Research and Prototyping
**Status:** Complete
Verified `list_repo_files` API and developed regex patterns for BibTeX and ArXiv extraction.

### Task 2: Implement Helper Logic
**Status:** Complete
Implemented `discover_relevant_links` in `server.py` with support for context capture and multiple link types.

### Task 3: Update Tool Response
**Status:** Complete
Refactored `fetch_hf_model_card` to use the new discovery logic and output a clean JSON checklist instead of automatically fetching content.

### Task 4: Add Tests
**Status:** Complete
Created `tests/test_link_discovery.py` covering Markdown, HTML, BibTeX, and Repo file discovery scenarios. All tests pass.

## Verification Results

**Automated tests:**
- `tests/test_link_discovery.py`: 5/5 passed
- Full suite: 72/72 passed

**Manual verification (conceptual):**
- Calling `fetch_hf_model_card` now returns the model card text followed by a JSON list of "DISCOVERED DOCUMENTS".
- No "EXTRA CONTEXT FETCHED FROM" sections appear, confirming automatic fetch is disabled.

## Self-Check: PASSED

**Modified files exist:**
```
FOUND: /Users/andrew/Antigravity/ai_act_compliance_mcp_server/server.py
```

**New files exist:**
```
FOUND: /Users/andrew/Antigravity/ai_act_compliance_mcp_server/tests/test_link_discovery.py
```

**All claims verified.**
