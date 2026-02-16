# Phase 2: MCP Tool Integration & File Management - Research

**Researched:** 2026-02-15
**Domain:** MCP tool development, file management, HTTP routing (FastMCP/Starlette)
**Confidence:** HIGH

## Summary

Phase 2 integrates PDF generation from Phase 1 with the existing MCP server by creating a new `generate_source_report` tool that mirrors the established `generate_compliance_doc` pattern. The implementation follows FastMCP best practices for tool definition, parameter validation, and multi-content responses (TextContent + EmbeddedResource). File management extends the existing cleanup thread to handle both .docx and .pdf files, and the download route automatically serves PDFs with correct MIME types using Starlette's FileResponse.

The existing codebase provides a complete reference implementation in `generate_compliance_doc` that can be directly adapted. The project already has all infrastructure in place: FastMCP server, Pydantic validation (citation_schema.py), PDF generator (pdf_generator.py), cleanup thread pattern, download route pattern, and Railway deployment configuration with environment variables.

**Primary recommendation:** Clone the `generate_compliance_doc` tool implementation and adapt it for PDF generation, using identical patterns for validation, file storage, response structure, and error handling.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| fastmcp | 2.14.4+ | MCP server framework | Official high-level framework for building MCP servers in Python with decorator-based tool definition |
| mcp | 1.25.0+ | MCP protocol types | Official Python SDK for Model Context Protocol providing types.TextContent, types.EmbeddedResource, types.BlobResourceContents |
| pydantic | 2.12.5+ | JSON validation | De facto standard for Python data validation with automatic JSON parsing via model_validate_json() |
| starlette | 0.52.1+ | HTTP routing | FastMCP's underlying ASGI framework for custom routes and FileResponse handling |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| base64 | stdlib | Binary encoding | Encoding PDF bytes for EmbeddedResource blob fields |
| uuid | stdlib | Unique IDs | Generating collision-resistant filenames with uuid4().hex |
| threading | stdlib | Background tasks | Running cleanup daemon threads for TTL-based file deletion |
| os | stdlib | File operations | File system operations (stat, listdir, remove) and environment variable access |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| FastMCP | Raw MCP SDK | FastMCP provides decorator-based tool definition and automatic schema generation; raw SDK requires manual protocol handling |
| Pydantic v2 | JSON schema validators | Pydantic v2 with Rust core is 5-50x faster and provides field validators for complex validation logic |
| threading | asyncio background tasks | threading.Thread daemon=True pattern is simpler for periodic cleanup; asyncio requires event loop management |

**Installation:**
All dependencies already in requirements.txt. No new packages needed for Phase 2.

## Architecture Patterns

### Recommended Project Structure
Current structure is optimal:
```
.
├── server.py                     # MCP server with @mcp.tool() definitions
├── pdf_generator.py              # Pure functions for PDF generation
├── citation_schema.py            # Pydantic models for validation
├── run_http_server.py            # HTTP server entry point with CORS
├── tests/
│   ├── test_pdf_generator.py    # Unit tests for PDF generation
│   └── test_citation_schema.py  # Unit tests for validation
└── fonts/
    └── DejaVuSans.ttf            # Unicode font for PDFs
```

### Pattern 1: MCP Tool with Multi-Content Response
**What:** Tool returns list[types.TextContent | types.EmbeddedResource] for both human-readable message and downloadable binary
**When to use:** Any tool that generates files for download
**Example:**
```python
# Source: Existing generate_compliance_doc tool in server.py
import mcp.types as types
import base64

@mcp.tool()
def generate_source_report(source_citations_json: str) -> list[types.TextContent | types.EmbeddedResource]:
    """
    Generate PDF citation report from JSON.
    Returns download link + embedded PDF.
    """
    # 1. Validate JSON with Pydantic
    try:
        report = validate_citation_json(source_citations_json)
    except ValueError as e:
        return [types.TextContent(type="text", text=f"Validation Error: {e}")]

    # 2. Generate PDF to memory buffer
    buffer = BytesIO()
    generate_source_report_pdf(buffer, [c.model_dump() for c in report.citations])
    pdf_bytes = buffer.getvalue()

    # 3. Save to DATA_DIR with unique filename
    filename = f"{model_name}_sources_{uuid.uuid4().hex[:6]}.pdf"
    output_path = os.path.join(DATA_DIR, filename)
    with open(output_path, "wb") as f:
        f.write(pdf_bytes)

    # 4. Encode as base64
    pdf_b64 = base64.b64encode(pdf_bytes).decode('utf-8')

    # 5. Build download URL
    base_url = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "")
    if base_url and not base_url.startswith("http"):
        base_url = f"https://{base_url}"
    full_link = f"{base_url}/download/{filename}"

    # 6. Return both TextContent (link) and EmbeddedResource (binary)
    return [
        types.TextContent(
            type="text",
            text=f"SUCCESS: PDF generated.\n\nDOWNLOAD LINK:\n{full_link}\n\n(Link active for 24 hours)"
        ),
        types.EmbeddedResource(
            type="resource",
            resource=types.BlobResourceContents(
                blob=pdf_b64,
                mimeType="application/pdf",
                uri=f"file:///{filename}"
            )
        )
    ]
```

### Pattern 2: Pydantic JSON Validation at Tool Boundary
**What:** Use Pydantic model_validate_json() to parse and validate JSON string parameters before processing
**When to use:** All tools accepting JSON string parameters
**Example:**
```python
# Source: citation_schema.py validate_citation_json function
from pydantic import ValidationError

def validate_citation_json(json_string: str) -> CitationReport:
    """Validate JSON string and return CitationReport instance."""
    try:
        return CitationReport.model_validate_json(json_string)
    except ValidationError as e:
        # Format field-level errors for user clarity
        error_messages = []
        for error in e.errors():
            field_path = " -> ".join(str(loc) for loc in error['loc'])
            error_messages.append(f"{field_path}: {error['msg']} (type: {error['type']})")
        raise ValueError("; ".join(error_messages))
```

**Why this pattern:**
- model_validate_json() is 5-50x faster than json.loads() + validation (Pydantic v2 Rust core)
- Produces field-level error messages with paths (e.g., "citations -> 0 -> confidence: Invalid enum value")
- Single call performs both parsing and validation atomically

### Pattern 3: Background Cleanup Thread
**What:** Daemon thread runs periodic cleanup of old files using TTL (time-to-live) based on mtime
**When to use:** Any server generating temporary files with known retention period
**Example:**
```python
# Source: Existing cleanup_old_files() in server.py (extend for .pdf)
import time
import threading
import os

def cleanup_old_files():
    """Delete .docx and .pdf files older than 24 hours."""
    while True:
        try:
            now = time.time()
            retention_seconds = 24 * 3600  # 24 hours

            if os.path.exists(DATA_DIR):
                for filename in os.listdir(DATA_DIR):
                    file_path = os.path.join(DATA_DIR, filename)
                    # Check both .docx and .pdf files
                    if os.path.isfile(file_path) and filename.endswith((".docx", ".pdf")):
                        stat = os.stat(file_path)
                        if now - stat.st_mtime > retention_seconds:
                            try:
                                os.remove(file_path)
                                print(f"CLEANUP: Deleted expired file {filename}")
                            except Exception as e:
                                print(f"CLEANUP ERROR: Could not delete {filename}: {e}")
        except Exception as e:
            print(f"CLEANUP FATAL ERROR: {e}")

        time.sleep(3600)  # Run every hour

# Start as daemon (terminates with main process)
cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
cleanup_thread.start()
```

**Why daemon=True:**
- Daemon threads terminate automatically when main process exits
- No need for graceful shutdown signaling for periodic cleanup
- Acceptable resource cleanup delay (files remain until next cycle)

### Pattern 4: Content-Type Aware File Serving
**What:** FileResponse automatically sets Content-Type based on file extension
**When to use:** Serving files with standard MIME types (.pdf, .docx, .png, etc.)
**Example:**
```python
# Source: Existing /download/{filename} route in server.py
from starlette.requests import Request
from starlette.responses import FileResponse, Response

@mcp.custom_route("/download/{filename}", methods=["GET"])
async def download_file(request: Request) -> Response:
    filename = request.path_params.get("filename")

    # Security: prevent path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        return Response("Invalid filename", status_code=400)

    file_path = os.path.join(DATA_DIR, filename)

    # Security: ensure resolved path is within DATA_DIR
    if not os.path.commonpath([os.path.abspath(file_path), DATA_DIR]) == DATA_DIR:
        return Response("Access denied", status_code=403)

    if not os.path.exists(file_path):
        return Response("File not found or expired", status_code=404)

    # FileResponse automatically sets Content-Type based on extension
    # .pdf -> application/pdf, .docx -> application/vnd.openxmlformats-officedocument.wordprocessingml.document
    return FileResponse(file_path, filename=filename)
```

**Why FileResponse auto-detects:**
- Starlette uses mimetypes stdlib module to map extensions to MIME types
- No manual Content-Type setting needed for common file types
- Browser receives correct Content-Type for proper download/display behavior

### Anti-Patterns to Avoid
- **Creating new Pydantic models for PDF tool:** Reuse existing CitationReport from citation_schema.py. Phase 1 already defined the data contract.
- **Manual JSON parsing before validation:** Don't use json.loads() then validate. Use model_validate_json() directly for performance and atomicity.
- **Hardcoding base URL in responses:** Always use RAILWAY_PUBLIC_DOMAIN environment variable or fallback to server_config.json for cloud/local flexibility.
- **URL-safe base64 encoding:** Use standard base64.b64encode(), not base64.urlsafe_b64encode(), to avoid MCP validation errors (known SDK issue).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| MCP tool schema generation | Manual JSON-RPC schema for tool parameters | FastMCP @mcp.tool() decorator | Automatic schema generation from type hints and docstrings; handles parameter validation |
| JSON parameter validation | Manual try/except with json.loads() and field checks | Pydantic model_validate_json() | 5-50x faster with Rust core; automatic field-level error messages with paths |
| File cleanup scheduling | Custom job queue or APScheduler | threading.Thread daemon=True with time.sleep() | Simpler for single periodic task; no external dependencies; automatic termination |
| MIME type detection | Manual mapping of extensions to MIME types | Starlette FileResponse auto-detection | Uses Python stdlib mimetypes module; handles edge cases |
| Filename collision avoidance | Timestamp-based filenames or manual counter | uuid.uuid4().hex | Cryptographically random; practically zero collision risk even at scale |

**Key insight:** Python stdlib (threading, uuid, base64, os) + FastMCP framework provide all primitives needed. Adding job schedulers, custom serializers, or manual protocol handling introduces unnecessary complexity.

## Common Pitfalls

### Pitfall 1: Inconsistent Return Types Between Success and Error
**What goes wrong:** Tool returns list[Content] on success but single TextContent on error, causing type errors
**Why it happens:** Error paths use early return with single TextContent for convenience
**How to avoid:** Always return list[types.TextContent | types.EmbeddedResource] even for errors
**Warning signs:** Type checker errors, client-side crashes on error responses
**Solution:**
```python
# WRONG
if error:
    return types.TextContent(type="text", text="Error message")

# RIGHT
if error:
    return [types.TextContent(type="text", text="Error message")]
```

### Pitfall 2: Forgetting to Extract Model Name for Filename
**What goes wrong:** All PDFs named "compliance_doc_sources_abc123.pdf" instead of "Llama_3_sources_abc123.pdf"
**Why it happens:** Citation JSON doesn't have top-level model_name field
**How to avoid:** Accept optional model_name parameter in tool signature OR extract from citation data if present
**Warning signs:** Generic filenames making it hard to identify which report belongs to which model
**Solution:**
```python
@mcp.tool()
def generate_source_report(source_citations_json: str, model_name: str = "model") -> list[...]:
    # Use model_name parameter in filename generation
    safe_name = "".join(x for x in model_name if x.isalnum() or x in (' ', '_', '-')).strip().replace(' ', '_')
    filename = f"{safe_name}_sources_{uuid.uuid4().hex[:6]}.pdf"
```

### Pitfall 3: Not Testing Cleanup Thread with Both File Types
**What goes wrong:** Cleanup thread hardcoded to delete only .docx files, PDFs accumulate indefinitely
**Why it happens:** Copy-paste from existing cleanup code that checks `filename.endswith(".docx")`
**How to avoid:** Update endswith() check to tuple: `filename.endswith((".docx", ".pdf"))`
**Warning signs:** Disk usage grows over time, only .docx files get deleted
**Solution:**
```python
# WRONG
if filename.endswith(".docx"):

# RIGHT
if filename.endswith((".docx", ".pdf")):
```

### Pitfall 4: URL-Safe Base64 Encoding for MCP
**What goes wrong:** MCP client validation fails with base64 decode error
**Why it happens:** Using base64.urlsafe_b64encode() which replaces + and / with - and _
**How to avoid:** Always use standard base64.b64encode() for EmbeddedResource blob fields
**Warning signs:** Client-side errors about invalid base64, validation failures in MCP protocol layer
**Solution:**
```python
# WRONG
pdf_b64 = base64.urlsafe_b64encode(pdf_bytes).decode('utf-8')

# RIGHT
pdf_b64 = base64.b64encode(pdf_bytes).decode('utf-8')
```

### Pitfall 5: Missing RAILWAY_PUBLIC_DOMAIN Environment Variable
**What goes wrong:** Download links show as "/download/file.pdf" instead of full URL
**Why it happens:** Railway environment variable not checked, or checked but not formatted as URL
**How to avoid:** Check for RAILWAY_PUBLIC_DOMAIN, prepend "https://" if missing scheme, fallback to server_config.json
**Warning signs:** Relative download links in production, users can't access files
**Solution:**
```python
# Get from environment
base_url = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "")
if base_url and not base_url.startswith("http"):
    base_url = f"https://{base_url}"

# Fallback to config file
if not base_url:
    try:
        with open("server_config.json", "r") as f:
            config = json.load(f)
            base_url = config.get("public_url", "").rstrip("/")
    except Exception:
        pass

# Construct full link
full_link = f"{base_url}/download/{filename}" if base_url else f"/download/{filename}"
```

## Code Examples

Verified patterns from existing codebase:

### Tool Definition with JSON Parameter Validation
```python
# Source: server.py generate_compliance_doc() (adapt for PDF)
import mcp.types as types
from citation_schema import validate_citation_json
from pdf_generator import generate_source_report_pdf
from io import BytesIO
import base64
import uuid
import os

@mcp.tool()
def generate_source_report(source_citations_json: str, model_name: str = "model") -> list[types.TextContent | types.EmbeddedResource]:
    """
    Generate PDF citation report from validated JSON.

    Args:
        source_citations_json: JSON string with citations array
        model_name: Optional model name for filename (default: "model")

    Returns:
        List containing TextContent (download link) and EmbeddedResource (base64 PDF)
    """
    # Validate JSON using Pydantic schema from Phase 1
    try:
        report = validate_citation_json(source_citations_json)
    except ValueError as e:
        return [types.TextContent(type="text", text=f"Validation Error: {e}")]

    # Generate PDF to memory buffer (no filesystem writes)
    try:
        buffer = BytesIO()
        generate_source_report_pdf(buffer, [c.model_dump() for c in report.citations])
        pdf_bytes = buffer.getvalue()
    except Exception as e:
        return [types.TextContent(type="text", text=f"PDF Generation Error: {e}")]

    # Sanitize model name and create filename with UUID
    safe_name = "".join(x for x in model_name if x.isalnum() or x in (' ', '_', '-')).strip().replace(' ', '_')
    short_name = safe_name[:30]  # Truncate to 30 chars
    random_suffix = uuid.uuid4().hex[:6]
    filename = f"{short_name}_sources_{random_suffix}.pdf"

    # Save to DATA_DIR for download
    output_path = os.path.join(DATA_DIR, filename)
    with open(output_path, "wb") as f:
        f.write(pdf_bytes)

    # Encode as standard base64 (not URL-safe)
    pdf_b64 = base64.b64encode(pdf_bytes).decode('utf-8')

    # Build public download URL
    base_url = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "")
    if base_url and not base_url.startswith("http"):
        base_url = f"https://{base_url}"

    if not base_url:
        try:
            with open("server_config.json", "r") as f:
                config = json.load(f)
                base_url = config.get("public_url", "").rstrip("/")
        except Exception:
            pass

    full_link = f"{base_url}/download/{filename}" if base_url else f"/download/{filename}"

    # Return both text and embedded binary
    return [
        types.TextContent(
            type="text",
            text=f"""SUCCESS: Source citation report generated.

DOWNLOAD LINK:
{full_link}

NOTE: This link will be active for 24 hours.
"""
        ),
        types.EmbeddedResource(
            type="resource",
            resource=types.BlobResourceContents(
                blob=pdf_b64,
                mimeType="application/pdf",
                uri=f"file:///{filename}"
            )
        )
    ]
```

### Extended Cleanup Thread for Multiple File Types
```python
# Source: server.py cleanup_old_files() (add .pdf support)
def cleanup_old_files():
    """
    Background thread that runs once an hour to delete files older than 24h.
    Handles both .docx and .pdf files.
    """
    while True:
        try:
            now = time.time()
            retention_seconds = 24 * 3600  # 24 hours

            if os.path.exists(DATA_DIR):
                for filename in os.listdir(DATA_DIR):
                    file_path = os.path.join(DATA_DIR, filename)
                    # CHANGE: Check for both .docx and .pdf files
                    if os.path.isfile(file_path) and filename.endswith((".docx", ".pdf")):
                        stat = os.stat(file_path)
                        if now - stat.st_mtime > retention_seconds:
                            try:
                                os.remove(file_path)
                                print(f"CLEANUP: Deleted expired file {filename}")
                            except Exception as e:
                                print(f"CLEANUP ERROR: Could not delete {filename}: {e}")
        except Exception as e:
            print(f"CLEANUP FATAL ERROR: {e}")

        time.sleep(3600)  # Sleep for 1 hour
```

### Content-Type Aware Download Route (No Changes Needed)
```python
# Source: server.py /download/{filename} (already handles .pdf automatically)
@mcp.custom_route("/download/{filename}", methods=["GET"])
async def download_file(request: Request) -> Response:
    """
    Serves both .docx and .pdf files with correct Content-Type.
    FileResponse auto-detects MIME type from extension.
    """
    filename = request.path_params.get("filename")

    # Security: prevent path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        return Response("Invalid filename", status_code=400)

    file_path = os.path.join(DATA_DIR, filename)

    # Security: ensure resolved path is within DATA_DIR
    if not os.path.commonpath([os.path.abspath(file_path), DATA_DIR]) == DATA_DIR:
        return Response("Access denied", status_code=403)

    if not os.path.exists(file_path):
        return Response("File not found or expired", status_code=404)

    # FileResponse automatically sets:
    # - application/pdf for .pdf files
    # - application/vnd.openxmlformats-officedocument.wordprocessingml.document for .docx
    return FileResponse(file_path, filename=filename)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual JSON-RPC schemas | FastMCP decorator-based tools | FastMCP 2.0+ (2025) | Automatic schema generation from type hints |
| Pydantic v1 | Pydantic v2 with Rust core | Pydantic v2.0 (2023) | 5-50x performance improvement for JSON parsing |
| URL-safe base64 for MCP | Standard base64 encoding | MCP SDK issue #342 (2025) | Avoid client validation errors |
| UUID4 random IDs | RFC 9562 UUID7 (timestamp+random) | RFC 9562 (2024) | Sortable UUIDs, but UUID4 still safe for filenames |
| Manual MIME type mapping | Starlette FileResponse auto-detect | Starlette 0.50+ | Simplified file serving |

**Deprecated/outdated:**
- urlsafe_b64encode for MCP blob fields: Use standard b64encode to avoid validation errors
- Manual JSON parsing before Pydantic: Use model_validate_json() directly for atomic parse+validate
- APScheduler for single periodic task: threading.Thread daemon=True is simpler for cleanup

## Open Questions

1. **Should model_name be required or optional parameter?**
   - What we know: Existing generate_compliance_doc extracts model_name from JSON data
   - What's unclear: Citation JSON schema doesn't include model_name field
   - Recommendation: Make it optional parameter with default "model", require caller to provide it

2. **Should cleanup thread deletion be configurable (TTL, file patterns)?**
   - What we know: Current hardcoded 24-hour TTL works for existing use case
   - What's unclear: Whether future phases need different TTL or cleanup patterns
   - Recommendation: Keep hardcoded for Phase 2, refactor to config if needed in later phases

3. **Should tool validate model_name for safe filename characters?**
   - What we know: Existing code sanitizes model_name with regex
   - What's unclear: Whether to reject invalid model_name or silently sanitize
   - Recommendation: Silent sanitization matches existing pattern, consistent UX

## Sources

### Primary (HIGH confidence)
- FastMCP Tools Documentation - https://gofastmcp.com/servers/tools
- Railway Variables Reference - https://docs.railway.com/reference/variables
- Pydantic JSON Validation - https://docs.pydantic.dev/latest/concepts/json/
- Python threading documentation - https://docs.python.org/3/library/threading.html
- Python uuid module documentation - https://docs.python.org/3/library/uuid.html

### Secondary (MEDIUM confidence)
- GitHub: modelcontextprotocol/python-sdk - https://github.com/modelcontextprotocol/python-sdk
- MCP Error Handling Guide - https://mcpcat.io/guides/error-handling-custom-mcp-servers/
- MCP base64 encoding issue #342 - https://github.com/modelcontextprotocol/python-sdk/issues/342
- FastMCP HTTP Deployment - https://gofastmcp.com/deployment/http

### Tertiary (LOW confidence)
- Medium: MCP Error Handling Best Practices (2026) - https://medium.com/@sureshddm/mcp-error-handling-dont-let-your-tools-fail-silently-1b5e02fabe4c
- GeeksforGeeks: Python file cleanup patterns - https://www.geeksforgeeks.org/python/delete-files-older-than-n-days-in-python/

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries verified in existing requirements.txt with version numbers
- Architecture: HIGH - Existing codebase provides complete reference implementation (generate_compliance_doc pattern)
- Pitfalls: MEDIUM - Derived from code inspection and web research, not production incidents

**Research date:** 2026-02-15
**Valid until:** 2026-03-17 (30 days - stable domain with mature libraries)
