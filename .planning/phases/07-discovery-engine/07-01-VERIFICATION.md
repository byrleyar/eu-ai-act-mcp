# Phase 07 Plan 01 Verification

## Automated Tests
- [ ] `pytest tests/test_link_discovery.py`
- [ ] `pytest tests/test_source_report_tool.py` (ensure no regressions)

## Manual Verification

### 1. Link Discovery with Context
**Action**: Call `fetch_hf_model_card` for a model with many links (e.g., `meta-llama/Llama-3.1-8B-Instruct`).
**Expected**: Discovered links section appears at the end with JSON data. Each link includes prefix/suffix context.

### 2. Repo File Discovery
**Action**: Call `fetch_hf_model_card` for a model with a PDF in the repo (e.g., `MiniMaxAI/MiniMax-M2.5`).
**Expected**: The PDF file path is listed in the discovered documents JSON with type `repository_file`.

### 3. BibTeX Discovery
**Action**: Call `fetch_hf_model_card` for a model with a BibTeX citation.
**Expected**: The arXiv link or URL from the BibTeX is extracted correctly.

### 4. No Automatic Fetch
**Action**: Call `fetch_hf_model_card`.
**Expected**: The response does NOT contain the "EXTRA CONTEXT FETCHED FROM" sections, as fetching is now deferred.

## Discovery Engine Checklist
- [ ] Captures Markdown links.
- [ ] Captures HTML links.
- [ ] Captures BibTeX links.
- [ ] Lists Repository PDFs.
- [ ] Provides context for each web link.
