# External Integrations

**Analysis Date:** 2026-02-15

## APIs & External Services

**Hugging Face Hub:**
- ModelCard API - Fetches model card metadata from Hugging Face repository
  - SDK/Client: `huggingface_hub` 1.3.3
  - Implementation: `fetch_hf_model_card()` in `server.py:219-247`
  - Authentication: API key via HuggingFace library (automatic or token-based)
  - Rate limit: Subject to HuggingFace API rate limits
  - Fails gracefully with EntryNotFoundError/RepositoryNotFoundError

**External Document Fetch:**
- Arxiv Papers - Fetches PDF papers from arxiv.org
  - Method: HTTP GET with PDF conversion (abs/ -> pdf/)
  - Implementation: `fetch_extra_info()` in `server.py:73-157`
  - Max file size: 10MB (enforced in `server.py:95`)

- GitHub Raw Content - Fetches raw PDF files from GitHub repositories
  - Method: Converts github.com/blob/ URLs to raw.githubusercontent.com
  - Implementation: URL rewriting in `fetch_extra_info()` `server.py:103-105`
  - User-Agent: Mozilla/5.0 (Compliance-Bot/1.0)

- Generic PDF Links - Fetches any accessible PDF from web
  - Method: HTTP GET with streaming
  - Content validation: Checks Content-Type header
  - Timeout: 10 seconds per request
  - Implementation: `server.py:88-89`

**Text Extraction Services:**
- pdf extraction (local) - PyPDF library extracts text from downloaded PDFs
  - Limits extraction to first 15 pages for context
  - Implementation: `server.py:120-128`

## Data Storage

**Databases:**
- Not applicable - No persistent database used

**File Storage:**
- Local Filesystem (Persistent Volume)
  - Location: `RAILWAY_VOLUME_MOUNT_PATH` or `./generated_docs`
  - Stores: Generated DOCX compliance documents
  - File format: DOCX (Office Open XML)
  - Retention: 24 hours (auto-cleanup via background thread in `server.py:40-70`)
  - Cleanup mechanism: Background thread deletes files older than 24 hours
  - Safety: Only deletes .docx files, path traversal protection in `server.py:289-297`

**Caching:**
- Not applicable - No caching layer (all content generated on-demand)

## Authentication & Identity

**Auth Provider:**
- None required for end users
- Hugging Face API - Automatic/token-based (library handles)
  - Optional: HuggingFace API token can be configured
  - Used for accessing public model cards

**MCP Security:**
- DNS Rebinding Protection: Disabled
  - Configuration: `TransportSecuritySettings(enable_dns_rebinding_protection=False)`
  - Location: `server.py:21`
  - Reason: Allows Railway/Ngrok/localhost operation without strict host validation

## Monitoring & Observability

**Error Tracking:**
- None - No external error tracking service
- Console logging: Python print() statements throughout `server.py`
  - DEBUG logging for external URL fetches: `server.py:82, 84, 105`
  - CLEANUP logging for file deletion: `server.py:58-61`

**Logs:**
- Console/stdout output only
  - Uvicorn logs HTTP requests
  - Python print() statements for application events
  - No persistent log storage configured

## CI/CD & Deployment

**Hosting:**
- Railway (primary/recommended)
  - Procfile: `web: python run_http_server.py --host 0.0.0.0`
  - Volume support: `RAILWAY_VOLUME_MOUNT_PATH` for document persistence
  - Environment variables: `RAILWAY_PUBLIC_DOMAIN`, `RAILWAY_STATIC_URL`
  - See README.md for Railway deployment instructions

- Ngrok (for local testing/Claude Desktop integration)
  - Configuration: Update `server_config.json` with ngrok URL
  - Usage: `ngrok http 8000` exposes local server

- Docker (implied but not configured)
  - No Dockerfile present
  - Deployable to any Docker-compatible platform supporting Python 3.10

**CI Pipeline:**
- Not detected - No CI/CD configuration files present
- Manual deployment supported via Railway/Docker

## Environment Configuration

**Required env vars:**
- None strictly required - All have fallbacks
- Recommended for production:
  - `RAILWAY_PUBLIC_DOMAIN` or `RAILWAY_STATIC_URL` - For absolute download links
  - `RAILWAY_VOLUME_MOUNT_PATH` - For persistent storage (Railway automatically sets)
  - `PORT` - Custom HTTP port (default: 8000)

**Optional env vars:**
- HuggingFace token (automatic or explicit via library)
  - For accessing private/gated models
  - Library handles via environment or config

**Secrets location:**
- `.env` file (git-ignored, not committed)
- Environment variables (deployed to platform)
- No hardcoded secrets in codebase

## Webhooks & Callbacks

**Incoming:**
- `/mcp` (GET, POST) - MCP protocol endpoint
  - Handles JSON-RPC requests from Claude/MCP clients
  - Fixed to support both GET and POST via route patching in `run_http_server.py:12-21`

- `/sse` (OPTIONS, POST, GET) - Server-Sent Events endpoint
  - OPTIONS: CORS preflight handling in `server.py:304-313`
  - POST: Returns 200 (prevented 405 errors) in `server.py:315-320`
  - GET: SSE stream for real-time updates (FastMCP built-in)

- `/download/{filename}` (GET) - Document download endpoint
  - Custom route for serving generated DOCX files
  - Implementation: `server.py:284-302`
  - Security: Path traversal prevention, file existence validation

**Outgoing:**
- None - Server does not emit webhooks
- Internal: Background cleanup thread processes file system (no external calls)

## Data Flows

**Model Card Processing Flow:**

1. Client requests model card via `fetch_hf_model_card(model_id)` tool
2. HuggingFace API returns model card metadata
3. Extract links from model card text
4. Follow up to 2 relevant links (Arxiv, papers, docs)
5. Return enriched model card with source attribution

**Compliance Document Generation Flow:**

1. Claude processes model card answers compliance questions
2. Client calls `generate_compliance_doc(compliance_data_json)` tool
3. Server loads DOCX template from `templates/default_template.docx`
4. Fill template placeholders with compliance data
5. Save generated DOCX to persistent storage with unique filename
6. Return download link (absolute URL if public_url configured)
7. Background cleanup thread deletes files after 24 hours

**Supported External Content:**
- PDF Papers (Arxiv, GitHub, web)
- Model cards (Hugging Face linked models)
- HTML pages with structured data (not currently parsed)
- Limits: 10MB max file size, first 15 pages of PDFs, 12K chars per source

---

*Integration audit: 2026-02-15*
