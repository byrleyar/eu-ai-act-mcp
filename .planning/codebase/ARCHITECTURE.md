# Architecture

**Analysis Date:** 2026-02-15

## Pattern Overview

**Overall:** Model-View-Controller (MVC) with MCP (Model Context Protocol) Server pattern

**Key Characteristics:**
- Stateless request/response architecture using FastMCP framework
- Multi-step workflow orchestrated by Claude AI client
- External data enrichment from Hugging Face Hub and linked resources
- Document generation pipeline with template substitution
- Persistence layer for generated documents with automatic cleanup

## Layers

**Transport & Server Layer:**
- Purpose: Handle HTTP/MCP communication with Claude clients
- Location: `run_http_server.py`, `server.py` (routes/resources sections)
- Contains: FastMCP server initialization, CORS middleware, SSE endpoint handling, custom routes
- Depends on: Starlette, FastMCP framework
- Used by: Claude Desktop, Claude.ai via HTTP gateway

**Data Retrieval Layer:**
- Purpose: Fetch and enrich model metadata from external sources
- Location: `server.py` (functions: `fetch_hf_model_card`, `extract_and_enrich_model_card`, `fetch_extra_info`)
- Contains: Hugging Face API calls, PDF/link extraction, content filtering, source tracking
- Depends on: `huggingface_hub`, `requests`, `pypdf`
- Used by: Tool orchestration layer via `fetch_hf_model_card` tool

**Tool Orchestration Layer:**
- Purpose: Define MCP tools that Claude calls as part of the workflow
- Location: `server.py` (decorated with `@mcp.tool()`)
- Contains: Three main tools - `fetch_hf_model_card`, `get_compliance_requirements`, `generate_compliance_doc`
- Depends on: Data retrieval layer, document generation layer
- Used by: Claude AI (orchestrates the workflow)

**Document Generation Layer:**
- Purpose: Transform compliance data into Word documents using templates
- Location: `docx_generator.py` (functions: `fill_template`, `process_tables`)
- Contains: Template loading, placeholder substitution, nested table processing, checkbox handling
- Depends on: `python-docx` library
- Used by: `generate_compliance_doc` tool

**Storage & Cleanup Layer:**
- Purpose: Persist generated documents and manage their lifecycle
- Location: `server.py` (global: `DATA_DIR`, function: `cleanup_old_files`, route: `/download/{filename}`)
- Contains: File persistence logic, 24-hour retention cleanup thread, download endpoint with path traversal protection
- Depends on: OS file system, Threading
- Used by: Document generation layer, HTTP clients downloading documents

**Configuration & Context Layer:**
- Purpose: Load instructions, questions schema, and user context
- Location: `questions.json`, `context.md`, `server_config.json`, resource endpoints
- Contains: 50+ compliance questions with descriptions, custom LLM instructions, public URL configuration
- Depends on: File system
- Used by: Tool orchestration layer, Claude AI instructions

## Data Flow

**Model Card Fetching Workflow:**

1. User provides Hugging Face model ID to Claude
2. Claude calls `fetch_hf_model_card(model_id)` tool
3. Tool fetches model card from Hugging Face Hub API
4. `extract_and_enrich_model_card()` scans model card for relevant links
5. For each qualifying link (paper, technical report, linked model):
   - `fetch_extra_info()` downloads content (converts Arxiv URLs, handles GitHub PDFs)
   - Extracts text from PDFs (limited to 15 pages, capped at 12k chars)
   - Appends to enrichment buffer
6. Returns enriched model card with explicit source attribution

**Compliance Document Generation Workflow:**

1. Claude calls `get_compliance_requirements()` to retrieve question schema
2. Claude manually answers 50+ compliance questions based on fetched model card
3. Claude calls `generate_compliance_doc(compliance_data_json)` with answers
4. Tool parses JSON compliance data
5. Loads template from `templates/default_template.docx`
6. `fill_template()` processes all document paragraphs and nested tables
7. Substitutes placeholders `{{key}}` with values (converts yes/no to checkboxes)
8. Saves generated document to `DATA_DIR` with unique UUID suffix
9. Constructs download URL from Railway/Ngrok domain or config file
10. Returns embedded document + markdown link for user

**Background Cleanup Cycle:**

1. Daemon thread starts at server initialization
2. Every 1 hour: scans `DATA_DIR` for `.docx` files
3. Deletes files older than 24 hours
4. Logs cleanup operations

**State Management:**
- No persistent application state; stateless between requests
- Temporary state: Files in `DATA_DIR` (24-hour TTL)
- Configuration state: `server_config.json`, `questions.json`, `context.md` (loaded at startup)
- User state: Entirely managed by Claude (conversation context)

## Key Abstractions

**MCP Tool:**
- Purpose: Expose server capabilities as discrete callable functions to Claude
- Examples: `fetch_hf_model_card()`, `get_compliance_requirements()`, `generate_compliance_doc()`
- Pattern: Decorated with `@mcp.tool()`, returns text or resource types, used by Claude directly

**MCP Resource:**
- Purpose: Expose static data (instructions, context) accessed by Claude during reasoning
- Examples: `compliance-questions://`, `compliance-context://`
- Pattern: Decorated with `@mcp.resource()`, returns formatted instructional text

**Custom HTTP Route:**
- Purpose: Expose non-MCP endpoints for file download and CORS handling
- Examples: `/download/{filename}` (GET), `/sse` (OPTIONS/POST)
- Pattern: Decorated with `@mcp.custom_route()`, bypasses MCP protocol

**Enrichment Strategy:**
- Purpose: Selectively follow 1-2 high-value links from model card to gather context
- Implementation: Keyword matching (relevant: "paper", "arxiv", "technical report"; skip: "license", "discord")
- Result: Extended model card content with explicit source tracking

## Entry Points

**HTTP Server:**
- Location: `run_http_server.py`
- Triggers: `python run_http_server.py` (Railway, local HTTP server)
- Responsibilities: Initializes FastMCP app, patches MCP route for POST support, adds CORS middleware, starts Uvicorn on port 8000

**MCP Stdio Server:**
- Location: `server.py`
- Triggers: `fastmcp run server.py` (Claude Desktop local config)
- Responsibilities: Initializes FastMCP with DNS rebinding protection disabled, registers tools and resources

**MCP SSE Endpoint:**
- Path: `/mcp` (GET for stream, POST for JSON-RPC)
- Location: FastMCP's streamable HTTP app (auto-generated from server.py)
- Triggers: Claude.ai client connects via custom connector URL
- Responsibilities: Handles Server-Sent Events protocol for bidirectional communication

## Error Handling

**Strategy:** Explicit error messages returned to Claude with context for retry/recovery

**Patterns:**

- **Model Card Fetch Errors:** Catches `RepositoryNotFoundError`, `EntryNotFoundError` from Hugging Face API, returns friendly "Model not found" message
- **PDF/Link Fetch Errors:** Wraps in try-catch, returns `[Error fetching info from URL: ...]` placeholder, continues with available data
- **JSON Validation:** Catches `json.JSONDecodeError` in `generate_compliance_doc`, returns error message without crashing
- **Template File Errors:** Checks `os.path.exists()` before loading, returns error if template missing
- **Path Traversal Security:** Validates filename with `".." in filename` checks before file access
- **Large File Handling:** Rejects downloads >10MB with early return, prevents memory exhaustion
- **Background Cleanup:** Wraps cleanup loop in try-except, logs errors, continues running even if individual deletions fail

**No Exceptions Crash Server:** All tool endpoints return error messages instead of raising exceptions

## Cross-Cutting Concerns

**Logging:**
- Simple print statements to stdout (captured by Uvicorn/Docker logs)
- Prefixes: `"INFO:"` (startup), `"DEBUG:"` (link fetching), `"CLEANUP:"` (file deletion), `"ERROR:"` (failures)
- No structured logging library; intended for Railway/cloud log aggregation

**Validation:**
- Model ID validation: Delegated to Hugging Face Hub API (raises RepositoryNotFoundError)
- JSON validation: Manual `json.loads()` with error catching
- URL validation: Regex matching for markdown links `[label](url)` and HTML `<a href="">` tags
- Filename validation: Allowlist approach (alphanumeric, underscore, hyphen, space only; no path separators)
- Content-Length validation: Rejects files >10MB before download

**Authentication:**
- None required for public MCP endpoint
- Transport security: DNS rebinding protection disabled (required for Ngrok/Railway tunneling)
- CORS: Allow-all policy (`allow_origins=["*"]`)
- Path security: Validates download paths to prevent directory traversal

**Configuration:**
- Environment variables: `RAILWAY_VOLUME_MOUNT_PATH`, `RAILWAY_PUBLIC_DOMAIN`, `RAILWAY_STATIC_URL`
- Config file: `server_config.json` with `public_url` (for Ngrok/local)
- Fallback chain: Railway env var → Config file → Relative path fallback
- Context injection: `context.md` read into memory on first call, instructs Claude on workflow

---

*Architecture analysis: 2026-02-15*
