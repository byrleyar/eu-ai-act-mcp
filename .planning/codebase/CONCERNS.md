# Codebase Concerns

**Analysis Date:** 2026-02-15

## Tech Debt

**DNS Rebinding Protection Disabled:**
- Issue: DNS rebinding protection is explicitly disabled in FastMCP server initialization (`server.py` line 21)
- Files: `server.py:21`
- Impact: Security risk exposing the MCP server to DNS rebinding attacks. Attackers could manipulate DNS resolution to bypass CORS/origin checks. This is a critical vulnerability in production environments.
- Fix approach: Re-enable DNS rebinding protection by default. Only disable it for explicit local development use cases. Add environment variable to control this behavior rather than hardcoding it.

**Debug Print Statements in Production Code:**
- Issue: Multiple `print()` debug statements left in production code (`server.py` lines 82, 84, 105, 154)
- Files: `server.py:82, 84, 105, 154`
- Impact: Debug output pollutes logs and may expose sensitive information about URLs being fetched and errors. Makes it harder to distinguish actual application logic from temporary debugging.
- Fix approach: Replace `print()` calls with proper logging using Python's `logging` module. Use appropriate log levels (DEBUG, INFO, ERROR). Disable DEBUG logs in production via configuration.

**Broad Exception Handling:**
- Issue: Multiple bare `except Exception:` blocks that catch all exceptions indiscriminately (`server.py` lines 62, 111, 142, 153, 246, 281, 383, 420, 468, 481)
- Files: `server.py:62, 111, 142, 153, 246, 281, 383, 420, 468, 481`
- Impact: Masks unexpected errors and makes debugging difficult. Silently fails without proper error reporting. Can hide programming errors that should be fixed.
- Fix approach: Catch specific exception types. Log specific errors appropriately. Let unexpected exceptions propagate or handle them at a higher level with proper context.

**No Input Validation on File Paths:**
- Issue: Path traversal protection exists (`server.py:289-290, 296-297`) but validation is minimal. The check `if ".." in filename or "/" in filename` is insufficient and can be bypassed.
- Files: `server.py:284-302`
- Impact: Potential directory traversal vulnerability allowing access to files outside intended `DATA_DIR`. An attacker could craft filenames like `..%2fpassword.txt` or use symlinks.
- Fix approach: Use `pathlib.Path.resolve()` to canonicalize paths and verify they're within `DATA_DIR` after resolution. Use `os.path.commonpath()` more robustly with absolute paths verified before comparison.

**Hardcoded Configuration Values:**
- Issue: Magic numbers and string literals scattered throughout code: 15 pages limit (`server.py:124`), 12k char truncation (`server.py:147`), 10MB file size limit (`server.py:95`), 2 fetch limit (`server.py:190`), 3600s cleanup interval (`server.py:66`)
- Files: `server.py:95, 124, 147, 190, 66`
- Impact: Configuration is not centralized, making it difficult to adjust limits without code changes. Different teams might have different configuration needs.
- Fix approach: Move all configuration constants to a dedicated config file or environment variables. Create a `Config` class with clear documentation of what each value controls.

**Inadequate Request Timeout Handling:**
- Issue: Fixed 10-second timeout on all external HTTP requests (`server.py:88, 108`) may be too short for large PDFs or too long for simple links.
- Files: `server.py:88, 108`
- Impact: Either fails on slow but legitimate requests, or times out late on very slow connections. No exponential backoff or retry logic.
- Fix approach: Implement configurable timeouts per request type. Add retry logic with exponential backoff for transient failures. Separate connection timeout from read timeout.

**File Cleanup Thread Never Stops:**
- Issue: Daemon thread running cleanup loop indefinitely with no shutdown mechanism (`server.py:40-70`)
- Files: `server.py:40-70`
- Impact: Thread runs even when server is shutting down. No graceful shutdown. On long-running deployments, thread accumulates resources or causes unclean shutdowns.
- Fix approach: Use proper thread lifecycle management. Implement a shutdown signal (e.g., threading.Event) that the cleanup loop checks. Register cleanup as an atexit handler or use proper ASGI lifecycle hooks.

**No Request Rate Limiting:**
- Issue: No rate limiting on fetch_extra_info or generate_compliance_doc endpoints
- Files: `server.py:73-157, 323-421`
- Impact: User could abuse the API to download entire internet (bypassing file size check) or generate unlimited documents, consuming server resources and storage.
- Fix approach: Add rate limiting per IP/user. Implement quotas for file generation and external fetches per time period. Add authentication or API key requirement.

## Known Bugs

**Text Replacement Doesn't Handle Partial Matches:**
- Bug: Template replacement in `docx_generator.py:24, 54` uses simple string replacement on paragraph.text
- Files: `docx_generator.py:24, 54`
- Symptoms: If a placeholder appears multiple times in a paragraph, or if a value contains the placeholder text, replacement can fail or cause corrupted output
- Trigger: Model name containing `}}` or value containing placeholder syntax like `{{key}}`
- Workaround: Sanitize model names to not contain placeholder syntax

**Broken Paragraph-Level Text Replacement:**
- Bug: python-docx's `paragraph.text` is read-only; modifying it doesn't update the document
- Files: `docx_generator.py:24, 54`
- Symptoms: Template placeholders in Word documents are not actually replaced; document generated but blanks remain
- Trigger: Any template with `{{placeholder}}` syntax in paragraphs
- Workaround: None - this is a fundamental issue with the approach. Should iterate through paragraph.runs instead.
- Fix approach: Rewrite replacement logic to work with `paragraph.runs` (the text segments within a paragraph) instead of `paragraph.text`.

**PDF Extraction Loses Formatting:**
- Bug: `pypdf.PdfReader` extracts text but loses all formatting and structure
- Files: `server.py:120-128`
- Symptoms: Extracted PDF content appears garbled or loses logical structure, making it harder for LLM to understand
- Trigger: Any PDF with complex formatting, columns, or special characters
- Workaround: Use better PDF extraction library (pdfplumber, PyPDF4) or OCR (tesseract)

**Content Truncation Loses Context:**
- Bug: Arbitrary truncation at 12k characters (`server.py:147-149`) may cut off mid-sentence or mid-table
- Files: `server.py:147-149`
- Symptoms: Model context incomplete, LLM can't answer questions about truncated sections
- Trigger: Any PDF over 12k chars
- Workaround: None - content is lost
- Fix approach: Use token counting instead of character counting. Implement smarter chunking that preserves semantic boundaries.

**GitHub Blob URL Conversion is Fragile:**
- Bug: URL manipulation for GitHub PDFs assumes specific format (`server.py:103-105`)
- Files: `server.py:103-105`
- Symptoms: Fails if URL structure slightly different or if GitHub changes URL format
- Trigger: GitHub URLs not matching exact pattern `github.com/.../blob/.../*.pdf`
- Workaround: Use GitHub API to fetch raw file content instead of URL manipulation

**Unsafe JSON Parsing Without Schema Validation:**
- Bug: `generate_compliance_doc` parses JSON but doesn't validate against expected schema (`server.py:340`)
- Files: `server.py:340`
- Symptoms: Invalid data passes through, generating documents with incomplete or wrong fields
- Trigger: Malformed JSON or missing required fields
- Workaround: None - document generated with missing data
- Fix approach: Use pydantic models to validate JSON schema before processing.

## Security Considerations

**No Authentication on MCP Server:**
- Risk: Anyone with network access to the server can generate compliance documents using arbitrary model cards and fetch external URLs
- Files: `server.py` (entire server)
- Current mitigation: None
- Recommendations:
  - Implement API key authentication for production deployments
  - Add allowlist of approved model IDs
  - Log all document generation with timestamps and model IDs
  - Restrict external URL fetching to approved domains/patterns

**Arbitrary External URL Fetching:**
- Risk: `fetch_extra_info` downloads any HTTP/HTTPS URL the LLM specifies. Could be used for SSRF attacks, to fetch internal network resources, or to bypass firewall
- Files: `server.py:73-157`
- Current mitigation: 10MB file size limit, 10-second timeout, limited to 2 fetches
- Recommendations:
  - Add domain allowlist (only arxiv.org, huggingface.co, github.com)
  - Block local network ranges (127.0.0.1, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
  - Use a proxy/gateway for outbound requests
  - Log all external fetches with full URL

**User-Agent Spoofing:**
- Risk: Fake User-Agent header (`server.py:87`) could be used to bypass bot detection
- Files: `server.py:87`
- Current mitigation: None
- Recommendations:
  - Use truthful User-Agent that identifies this as an automated compliance tool
  - Don't spoof as Firefox/Chrome

**Weak File Path Validation:**
- Risk: Path traversal despite checks (see Tech Debt section)
- Files: `server.py:284-302`
- Current mitigation: Basic string checks for "..", "/", "\"
- Recommendations: Rewrite using pathlib.Path with proper canonicalization and verification

**No HTTPS Enforcement:**
- Risk: HTTP mode allows man-in-the-middle attacks on compliance data
- Files: `run_http_server.py` (allows unencrypted HTTP)
- Current mitigation: None
- Recommendations:
  - Enforce HTTPS in production (use Railway's HTTPS automatically)
  - Add HSTS headers
  - Never allow HTTP fallback

**Model Card Content Execution Risk:**
- Risk: Model cards can contain arbitrary markdown/HTML that gets echoed back to LLM unvalidated
- Files: `server.py:228-242`
- Current mitigation: None
- Recommendations:
  - Sanitize HTML from model cards
  - Don't trust markdown links - validate before fetching
  - Strip executable content (scripts, iframes)

## Performance Bottlenecks

**Synchronous PDF Processing:**
- Problem: PDF extraction blocks request handling while processing (`server.py:116-128`)
- Files: `server.py:116-128`
- Cause: Using synchronous `requests.get()` and `PdfReader` in request handler
- Impact: If multiple users request documents, processing queues up and some requests timeout
- Improvement path:
  - Use async HTTP client (httpx with async)
  - Process PDFs in background queue (Celery, RQ)
  - Return document ID and poll for status instead of blocking

**No Caching of Model Cards:**
- Problem: Every call fetches from HuggingFace, even if same model requested multiple times
- Files: `server.py:225-227`
- Cause: No caching layer
- Impact: Slow performance, wasted bandwidth, HuggingFace API rate limits
- Improvement path:
  - Cache model cards in-memory or Redis
  - Cache with TTL (1-24 hours)
  - Cache at HTTP level with Cache-Control headers

**N+1 HTTP Requests:**
- Problem: For each link in model card, makes separate HTTP request to check headers, then another to fetch content
- Files: `server.py:85-157`
- Cause: Check headers first with `response.headers.get()` before reading body
- Impact: Doubles latency on models with many links
- Improvement path:
  - Stream-read headers and body in single request
  - Use HEAD request for size check before GET

**No Async Support:**
- Problem: All document generation is synchronous, blocking the event loop
- Files: `run_http_server.py:36, server.py` (all tools)
- Cause: Using uvicorn but not async/await
- Impact: Single slow request blocks entire server
- Improvement path:
  - Make tools async where possible
  - Use thread pool for I/O operations
  - Implement proper concurrent request handling

## Fragile Areas

**Word Document Template Replacement Logic:**
- Files: `docx_generator.py:12-58, server.py:323-421`
- Why fragile:
  - Uses simple string replacement on `paragraph.text` which is read-only
  - No handling for multi-run paragraphs
  - No handling for tables with merged cells
  - No validation that placeholder exists before replacement
- Safe modification:
  - Rewrite to iterate through `paragraph.runs` instead of `paragraph.text`
  - Add unit tests for various template structures
  - Add validation that all placeholders are replaced
  - Consider using python-docx's XMLElement API for more robust replacement
- Test coverage gaps: No tests for actual template filling. No tests for edge cases like special characters in values.

**External URL Fetching with Regex Matching:**
- Files: `server.py:73-157`
- Why fragile:
  - Regex patterns for markdown/HTML links may not match all variations
  - ArXiv URL conversion hardcoded
  - GitHub URL conversion hardcoded
  - No error recovery if fetched content is malformed
  - Assumes specific URL patterns
- Safe modification:
  - Use an HTML parser library instead of regex for HTML links
  - Use a markdown parser library for markdown links
  - Add unit tests for various URL formats
  - Add provider-specific fetcher classes
- Test coverage gaps: No tests for URL parsing. No tests for edge case URLs.

**File Cleanup Thread:**
- Files: `server.py:40-70`
- Why fragile:
  - No exception handling in cleanup loop (can crash silently if /DATA_DIR is deleted)
  - No logging of cleanup success/failure
  - Hardcoded 24-hour retention
  - Files only checked once per hour - could accumulate
  - No metrics or monitoring
- Safe modification:
  - Add proper exception handling and logging
  - Make retention configurable
  - Add monitoring/alerting
  - Use proper lifecycle management (not daemon threads)
- Test coverage gaps: No tests for cleanup logic. No tests for behavior when directory doesn't exist.

**Model Card Enrichment Logic:**
- Files: `server.py:159-216`
- Why fragile:
  - Hardcoded list of keywords that may miss relevant links
  - Only fetches 2 links - may not be enough for complex models
  - No deduplication if same URL appears twice
  - Fetches happen sequentially - slow
  - No validation that fetched content is actually relevant
- Safe modification:
  - Make keyword lists configurable
  - Add ML-based link relevance scoring
  - Implement parallel fetching with semaphore
  - Cache fetched content
- Test coverage gaps: No tests for link selection logic. No tests for content enrichment.

**Environment Variable Fallback Chain:**
- Files: `server.py:29-33, 371-384`
- Why fragile:
  - Multiple configuration sources with complex precedence (RAILWAY_VOLUME_MOUNT_PATH, RAILWAY_PUBLIC_DOMAIN, RAILWAY_STATIC_URL, server_config.json)
  - No logging of which config source was actually used
  - Silent fallback if all fail (uses relative path)
  - Config file parsing doesn't handle missing keys gracefully
- Safe modification:
  - Log which configuration was loaded
  - Validate configuration at startup
  - Fail fast if critical config is missing
  - Use environment variable loader library with validation
- Test coverage gaps: No tests for different configuration scenarios.

## Scaling Limits

**Single-Thread Cleanup:**
- Current capacity: 1 file cleanup check per hour
- Limit: If files accumulate faster than cleanup (> 1 file per minute on average), disk fills up before next cleanup runs
- Files: `server.py:40-70`
- Scaling path:
  - Check cleanup every 5-10 minutes instead of hourly
  - Run cleanup asynchronously with concurrent.futures
  - Monitor disk usage and alert if threshold exceeded
  - Use object storage (S3) instead of local filesystem for unlimited scale

**In-Memory Storage of Large PDFs:**
- Current capacity: Limited by available RAM
- Limit: PDFs fetched into `io.BytesIO()` buffer in memory. 10MB limit per file × 2 files × concurrent requests
- Files: `server.py:116-118`
- Scaling path:
  - Stream PDF processing instead of loading into memory
  - Use temporary files instead of BytesIO
  - Implement request queuing to limit concurrent processing

**No Database for Document Tracking:**
- Current capacity: Only filesystem with 24h cleanup
- Limit: No way to query what documents were generated, by whom, when. Storage eventually fills up.
- Files: `server.py:40-70`
- Scaling path:
  - Add database to track generated documents
  - Enable audit logging
  - Implement tiered storage (hot/cold)
  - Add S3 integration for scalable storage

**Single-Process Server:**
- Current capacity: One Python process handling all requests
- Limit: CPU-bound PDF extraction blocks other requests. Can't use multiple cores.
- Files: `run_http_server.py:36`
- Scaling path:
  - Run multiple uvicorn workers (gunicorn, supervisor)
  - Use async processing
  - Offload heavy work to background task queue (Celery)

## Dependencies at Risk

**Pinned Dependencies Without Upper Bounds:**
- Risk: All packages pinned to exact versions. When packages reach end-of-life, security patches won't be installed.
- Files: `requirements.txt`
- Impact: Security vulnerabilities in outdated packages (e.g., pypdf==3.17.4 is old, may have known vulnerabilities)
- Migration plan:
  - Audit all dependencies for known CVEs
  - Switch to semantic versioning bounds (e.g., `pypdf>=3.17,<5.0`)
  - Set up Dependabot or renovate to auto-update
  - Add pre-commit hook to check for security issues

**PyPDF as PDF Extraction:**
- Risk: PyPDF is unmaintained and may have PDF handling bugs
- Files: `requirements.txt:97`, `server.py:16, 120`
- Impact: PDF extraction fails silently on complex PDFs, security issues in PDF parser
- Migration plan:
  - Evaluate pdfplumber or PyPDF2 as alternatives
  - Add unit tests for various PDF formats
  - Consider using cloud API (AWS Textract) for production

**python-docx for Document Generation:**
- Risk: python-docx doesn't support all Word features, text replacement is fundamentally broken (see Bugs section)
- Files: `requirements.txt:72`, `docx_generator.py`
- Impact: Generated documents may be corrupted or have missing content
- Migration plan:
  - Evaluate python-pptx or docxtpl as alternatives
  - Rewrite template filling to work at XML level if staying with python-docx
  - Consider using Word's mail-merge feature instead of custom replacement

**FastMCP Versioning:**
- Risk: FastMCP is young framework (v2.14.4). APIs may change significantly. Bug on line 10 of `run_http_server.py` suggests version-specific issues.
- Files: `requirements.txt:23`, `run_http_server.py:10`
- Impact: Upgrades may break the server. Workarounds for bugs become unmaintainable.
- Migration plan:
  - Pin to specific major version only (e.g., `fastmcp>=2.14,<3.0`)
  - Monitor FastMCP changelog for breaking changes
  - Have test suite that validates MCP protocol compliance

## Missing Critical Features

**No Logging System:**
- Problem: Using `print()` for logging. No structured logging, no log levels, no log rotation.
- Blocks: Debugging issues in production. Can't monitor for errors. Can't comply with audit requirements.
- Impact: When server fails, no way to know why.
- Fix approach:
  - Implement Python logging with JSON structured logs
  - Log to file with rotation
  - Add log aggregation (CloudWatch, DataDog, ELK)
  - Implement correlation IDs for tracing requests

**No Metrics/Monitoring:**
- Problem: No way to know if server is healthy, how many documents generated, API success rate
- Blocks: Production monitoring, alerting, capacity planning
- Impact: Server could be failing silently. Can't debug performance issues.
- Fix approach:
  - Add Prometheus metrics
  - Track: request count, error count, latency, document generation time
  - Add health check endpoint
  - Implement alerting on error rate threshold

**No Audit Trail:**
- Problem: No recording of who generated what document, when, from which model
- Blocks: Regulatory compliance, debugging, understanding usage patterns
- Impact: Can't trace which documents were generated when or why
- Fix approach:
  - Log all document generations with timestamp, model ID, user/IP
  - Store audit log in database
  - Implement document versioning

**No Input Sanitization:**
- Problem: Model names and values go directly into documents without sanitization
- Blocks: Can't prevent XSS, formula injection, or other attacks
- Impact: If model name contains malicious content, it could execute in generated document
- Fix approach:
  - Sanitize all user inputs before using in documents
  - Validate model ID format
  - Escape special characters in template values

**No Testing Framework:**
- Problem: No unit tests, integration tests, or test fixtures
- Blocks: Safe refactoring, regression prevention
- Impact: Any change could silently break functionality
- Fix approach:
  - Add pytest with >80% coverage
  - Add integration tests for each tool
  - Add fixtures for sample model cards and PDFs
  - Add end-to-end tests

## Test Coverage Gaps

**No Tests for PDF Extraction:**
- What's not tested: PDF parsing, text extraction, formatting preservation, error handling
- Files: `server.py:114-128`
- Risk: Could silently fail on edge case PDFs (scanned, password-protected, corrupted)
- Priority: High - core feature

**No Tests for URL Fetching:**
- What's not tested: Regex URL matching, URL validation, timeout handling, error recovery
- Files: `server.py:73-157`
- Risk: Could fail on URLs with special characters or unexpected formats
- Priority: High - feature is used frequently

**No Tests for Template Filling:**
- What's not tested: Placeholder replacement, special characters in values, missing placeholders, multi-run paragraphs
- Files: `docx_generator.py:30-59`
- Risk: Generated documents could be corrupted or have missing data
- Priority: Critical - core output

**No Tests for File Cleanup:**
- What's not tested: File deletion, thread behavior, error handling, concurrent access
- Files: `server.py:40-70`
- Risk: Files not deleted properly, disk fills up, race conditions
- Priority: Medium - impacts system stability

**No Tests for Configuration Loading:**
- What's not tested: Environment variables, config file parsing, fallback behavior
- Files: `server.py:29-33, 371-384`
- Risk: Wrong configuration loaded silently
- Priority: Medium - impacts all deployments

**No Tests for Path Validation:**
- What's not tested: Path traversal attempts, symbolic links, edge case filenames
- Files: `server.py:284-302`
- Risk: Security vulnerability in path handling
- Priority: Critical - security

**No Tests for JSON Parsing:**
- What's not tested: Malformed JSON, missing fields, type mismatches
- Files: `server.py:340`
- Risk: Invalid data passed to document generation
- Priority: Medium - impacts document quality

---

*Concerns audit: 2026-02-15*
