# Phase 08 Plan 01 Verification

## Automated Tests
- [ ] `pytest tests/test_document_fetch.py`
- [ ] `pytest tests/test_link_discovery.py` (ensure no regressions)

## Manual Verification

### 1. Fetch arXiv Paper
**Action**: Call `fetch_external_document` with an arXiv abstract URL (e.g., `https://arxiv.org/abs/2401.12345`).
**Expected**: Tool returns the extracted text from the PDF version of the paper.

### 2. Fetch HTML Page
**Action**: Call `fetch_external_document` with a standard documentation URL.
**Expected**: Tool returns the text content of the page.

### 3. SSRF Protection
**Action**: Call `fetch_external_document` with `http://localhost:8000` or `http://169.254.169.254`.
**Expected**: Tool returns an error message indicating the URL is unsafe or prohibited.

### 4. File Size Limit
**Action**: Call `fetch_external_document` with a URL pointing to a very large file (>10MB).
**Expected**: Tool returns an error message indicating the file is too large.

## Targeted Fetch Checklist
- [ ] Validates URL safety.
- [ ] Handles arXiv redirects.
- [ ] Extracts text from PDF (limited pages).
- [ ] Extracts text from HTML.
- [ ] Returns structured source header.
