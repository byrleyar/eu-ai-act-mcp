# Phase 08 Research: Targeted Fetch Tool

## Objective
Implement the `fetch_external_document` tool to allow on-demand retrieval and parsing of technical documents discovered in Phase 7.

## Key Requirements Analysis

### 1. Tool Interface (ACQ-04)
- **Tool Name**: `fetch_external_document`
- **Parameters**:
    - `url` (string, required): The URL of the document to fetch.
- **Output**:
    - `text`: Extracted text from the document.
    - `metadata`: Source URL, title (if available), content type.

### 2. PDF Extraction Quality (ACQ-05)
- Currently using `pypdf`.
- **Challenges**: Multi-column layouts in academic papers often lead to interleaved text if parsed line-by-line.
- **Strategy**: 
    - Ensure we extract text per-page.
    - Limit extraction to first 15-20 pages to avoid context bloat.
    - Use `pypdf` with reasonable defaults. If layout issues persist, we will document it as a limitation for now.

### 3. Safety & Rate Limiting (ACQ-06)
- **URL Validation**: 
    - Ensure URL is absolute and uses `http/https`.
    - Block local/private IPs (prevent SSRF) - check for localhost, 127.0.0.1, 10.x, 192.168.x etc.
- **Rate Limiting**: 
    - Basic implementation: 1 fetch per call (enforced by synchronous execution).
    - Max file size: 10MB (existing safeguard).
- **arXiv Handling**: 
    - Automatically convert `/abs/` to `/pdf/` for direct retrieval.

### 4. Code Reuse
- Re-implement the `fetch_extra_info` logic from Phase 6 but as a more robust tool.

## Implementation Details
- Add `fetch_external_document` tool to `server.py`.
- Improve the `requests` configuration (timeout, User-Agent).
- Implement a basic URL sanity check function.

## Verification Plan
- Unit tests for the URL parsing helper.
- Integration test for fetching a real arXiv PDF.
- Manual verification via MCP tool call.
