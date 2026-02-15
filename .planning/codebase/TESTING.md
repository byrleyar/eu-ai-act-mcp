# Testing Patterns

**Analysis Date:** 2026-02-15

## Test Framework

**Status:** No test framework detected

**Investigation Results:**
- No `pytest`, `unittest`, or `nose` configuration found
- No `pytest.ini`, `setup.cfg`, `tox.ini`, or `pyproject.toml` test configuration
- No test files present in codebase (`test_*.py` or `*_test.py` files not found)
- No test directory structure (`tests/`, `test/`)
- No mock or fixture libraries in requirements.txt
- Python 3.10+ required per `pyproject.toml` line 5

**Development Status:**
- Project is in early stage (version 0.1.0 in `pyproject.toml`)
- Focus is on core functionality delivery rather than automated testing
- Manual testing likely conducted through MCP protocol and HTTP endpoints

## Testing Approach

**Current State:**
- No automated test suite
- No test runner command configured
- No coverage tracking or CI/CD integration detected

**Entry Points for Manual Testing:**
1. MCP Tools (via `server.py`):
   - `fetch_hf_model_card()` - line 219
   - `get_compliance_requirements()` - line 250
   - `generate_compliance_doc()` - line 323

2. HTTP Routes (via `run_http_server.py`):
   - `GET /download/{filename}` - line 284
   - `POST /sse` - line 315
   - `OPTIONS /sse` - line 304

3. Resources (via MCP):
   - `compliance-questions://` - line 424
   - `compliance-context://` - line 471

## Code Organization for Testing

**Main Modules:**
- `server.py` - Contains core MCP tools and HTTP route handlers
- `docx_generator.py` - Contains document generation logic
- `run_http_server.py` - HTTP server configuration and startup

**Key Testable Functions:**

**In `server.py`:**
```python
# Lines 73-157: fetch_extra_info(url: str) -> str
# Responsibility: Fetch and parse external content (PDFs, model cards)
# Test points: URL validation, PDF extraction, truncation logic

# Lines 159-216: extract_and_enrich_model_card(text: str) -> tuple[str, list[str]]
# Responsibility: Find relevant links in model card text and fetch them
# Test points: Regex link extraction, keyword filtering, API calls

# Lines 40-66: cleanup_old_files()
# Responsibility: Background daemon to delete files older than 24 hours
# Test points: File age calculation, safe deletion (only .docx files)

# Lines 323-421: generate_compliance_doc(compliance_data_json: str)
# Responsibility: Convert JSON compliance data to DOCX file
# Test points: JSON parsing, template filling, file generation
```

**In `docx_generator.py`:**
```python
# Lines 6-10: load_docx_from_template(path_or_file) -> Document
# Responsibility: Load DOCX template from path or file object
# Test points: File handling, error cases

# Lines 12-28: process_tables(tables, display_data)
# Responsibility: Recursively replace placeholders in table cells
# Test points: Nested table handling, placeholder replacement

# Lines 30-59: fill_template(template_path, output_path, data: dict)
# Responsibility: Main document generation flow
# Test points: Template validation, data substitution, checkbox logic
```

## Mock/External Dependencies

**External APIs Called:**
1. **Hugging Face Hub** (lines 5-6, 219-247):
   ```python
   from huggingface_hub import ModelCard
   card = ModelCard.load(model_id)  # Requires network
   ```
   - Used in: `fetch_hf_model_card()`, `extract_and_enrich_model_card()`
   - Would need mocking in tests

2. **HTTP Requests** (line 14):
   ```python
   import requests
   response = requests.get(url, stream=True, timeout=10, headers=headers)
   ```
   - Used in: `fetch_extra_info()` for PDFs, Model Cards, Arxiv papers
   - Would need mocking with `responses` or `requests_mock`

3. **PDF Processing** (line 16):
   ```python
   from pypdf import PdfReader
   reader = PdfReader(f)
   ```
   - Used in: `fetch_extra_info()` PDF extraction
   - Would need sample PDF fixtures

4. **File I/O** (multiple locations):
   - Reading: `questions.json` (line 256), `context.md` (line 477), `server_config.json` (line 380)
   - Writing: `.docx` files to `DATA_DIR` (line 360)
   - Would need temporary directory fixtures (tmpdir)

**What Would Need Mocking:**
- `requests.get()` for HTTP calls
- `ModelCard.load()` for HF API
- `PdfReader` for PDF extraction
- File system operations (os.path, open())

**What Could Be Tested Without Mocks:**
- URL parsing logic (lines 77-81: Arxiv URL conversion)
- Regex link extraction (lines 165, 169)
- Keyword filtering logic (lines 202-211)
- String replacement and formatting logic
- JSON parsing edge cases

## Test Data & Fixtures

**Sample Model Card Needed:**
```python
# Would be stored in tests/fixtures/sample_model_card.md
# Contains:
# - Markdown links [Text](URL)
# - HTML links <a href="URL">Text</a>
# - Keywords: "paper", "arxiv", "documentation"
# - Skip keywords: "license", "twitter"
```

**Sample Questions JSON:**
```json
// Located at: questions.json
// Structure: Array of objects with 'id' and 'description' fields
// Would need copy for testing data mapping
```

**Sample Compliance Data:**
```python
# JSON structure matching questions.json schema
# Used to test generate_compliance_doc() function
# Example: {"model_name": "test-model", "field1": "value1", ...}
```

**File Fixtures Needed:**
- `default_template.docx` - Located at `templates/default_template.docx`
- Sample PDF files for extraction testing
- Configuration files: `server_config.json`

## Error Testing

**Error Scenarios in Code:**

**Network Errors:**
```python
# Lines 85-89: fetch_extra_info()
try:
    response = requests.get(url, stream=True, timeout=10, headers=headers)
    response.raise_for_status()
except Exception as e:
    return f"\n[Error fetching info from {url}: {str(e)}]"
```
- Timeout: URL takes >10 seconds
- Connection failure: Network unreachable
- HTTP errors: 404, 500, etc (handled by raise_for_status())

**File Not Found:**
```python
# Lines 466, 479: Resource functions
except FileNotFoundError:
    return "Error: questions.json not found"
```
- Missing questions.json
- Missing context.md
- Missing template file (line 336)

**JSON/Parsing Errors:**
```python
# Lines 339-342: generate_compliance_doc()
except json.JSONDecodeError as e:
    return [types.TextContent(type="text", text=f"Error: Invalid JSON...")]
```
- Malformed compliance_data_json parameter

**Security Validation:**
```python
# Lines 288-297: download_file() security checks
if ".." in filename or "/" in filename or "\\" in filename:
    return Response("Invalid filename", status_code=400)
if not os.path.commonpath([os.path.abspath(file_path), DATA_DIR]) == DATA_DIR:
    return Response("Access denied", status_code=403)
```
- Path traversal attempts
- Files outside DATA_DIR

## Recommended Test Structure

**If Testing Were Implemented**, use pytest with this structure:

```
tests/
├── conftest.py                          # Shared fixtures
├── fixtures/
│   ├── sample_model_card.md
│   ├── sample_questions.json
│   ├── default_template.docx
│   └── sample_pdfs/
├── unit/
│   ├── test_server.py                  # Test server.py functions
│   ├── test_docx_generator.py          # Test docx_generator.py
│   └── test_http_routes.py             # Test HTTP endpoints
├── integration/
│   ├── test_hf_integration.py          # Test HF Hub API calls
│   └── test_document_generation.py     # End-to-end doc generation
└── mocks/
    ├── mock_responses.py               # HTTP response mocks
    └── mock_hf_data.py                 # HF API mocks
```

**Fixture Example (conftest.py):**
```python
import pytest
from pathlib import Path
import tempfile

@pytest.fixture
def temp_data_dir():
    """Temporary directory for generated files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def sample_compliance_data():
    """Sample compliance JSON data"""
    return {
        "model_name": "test-model",
        "description": "Test compliance document"
    }

@pytest.fixture
def mock_requests(monkeypatch):
    """Mock requests.get for external URL calls"""
    import requests

    def mock_get(url, **kwargs):
        # Return sample data based on URL
        pass

    monkeypatch.setattr(requests, "get", mock_get)
```

## Coverage Recommendations

**High Priority (Most Critical):**
- `generate_compliance_doc()` - Core document generation
- `fill_template()` - Template filling logic
- Security checks in `download_file()` - Path traversal prevention

**Medium Priority:**
- `fetch_extra_info()` - URL fetching and parsing
- `extract_and_enrich_model_card()` - Link extraction logic
- `fetch_hf_model_card()` - API integration

**Lower Priority:**
- `cleanup_old_files()` - Background maintenance
- HTTP route handlers - Already handled by MCP framework
- Resource loaders - Simple file reading

## Current Testing Approach

**Manual Testing:**
1. Deploy to Railway or Ngrok
2. Call MCP tools through Claude interface
3. Verify generated DOCX files contain correct content
4. Test HTTP downloads work correctly
5. Verify 24-hour file cleanup works

**What's Missing:**
- Automated regression testing
- Unit test coverage
- Integration test suite
- CI/CD pipeline (no GitHub Actions, etc detected)
- Performance/load testing
- Security/vulnerability scanning

---

*Testing analysis: 2026-02-15*
