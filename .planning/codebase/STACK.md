# Technology Stack

**Analysis Date:** 2026-02-15

## Languages

**Primary:**
- Python 3.10 - Core server and MCP implementation
  - Specified in `runtime.txt`
  - Required minimum in `pyproject.toml`

## Runtime

**Environment:**
- Python 3.10 (CPython)
- Runs on Linux/macOS/Windows

**Package Manager:**
- pip/uv
- Lockfile: Not detected (requirements.txt used as primary manifest)

## Frameworks

**Core:**
- FastMCP 2.14.4 - MCP server framework built on Starlette
  - Location: `server.py` - Main server implementation
  - Provides HTTP and SSE support for MCP protocol

**Web/HTTP:**
- Starlette 0.52.1 - ASGI web framework
  - Used by FastMCP for HTTP routing and middleware
  - See `run_http_server.py` for HTTP server setup
  - CORS middleware configured in `run_http_server.py`

**Server/Async:**
- Uvicorn 0.40.0 - ASGI server
  - HTTP server runtime in `run_http_server.py`
  - Default port: 8000 (configurable via PORT env var)

**Testing/Dev:**
- No test framework detected - Project contains no test suite

## Key Dependencies

**Critical:**
- mcp 1.25.0 - MCP protocol implementation and types
  - Core: `from mcp.server.fastmcp import FastMCP`
  - Core: `from mcp.server.transport_security import TransportSecuritySettings`
  - Core: `import mcp.types as types`
  - Used in `server.py:1-2, 10`

- huggingface_hub 1.3.3 - Hugging Face API client
  - Used to fetch model cards: `from huggingface_hub import ModelCard`
  - Exception handling: `from huggingface_hub.utils import EntryNotFoundError, RepositoryNotFoundError`
  - Used in `server.py:5-6, 219-247`

- python-docx 1.2.0 - DOCX file generation and template filling
  - Used to load, modify, and save Word documents
  - See `docx_generator.py` - Template filling implementation
  - Used in `generate_compliance_doc()` function in `server.py:323-421`

**Infrastructure:**
- requests 2.32.5 - HTTP client for fetching external content
  - Fetches PDF files and external links
  - Used in `fetch_extra_info()` function in `server.py:73-157`
  - Handles GitHub raw URLs and Arxiv PDFs

- pypdf 3.17.4 - PDF reading and text extraction
  - Extracts text from PDF papers linked in model cards
  - Used in `fetch_extra_info()` function in `server.py:114-128`

- pydantic 2.12.5 - Data validation (transitive dependency)
  - Used by Starlette and MCP framework

**Utilities:**
- python-dotenv 1.2.0 - Environment variable loading
  - Not explicitly used in provided code, likely for .env support

- rich 14.2.0 - Terminal output formatting (transitive)

- httpx 0.28.1 - Alternative HTTP client (transitive)

## Configuration

**Environment:**
- RAILWAY_VOLUME_MOUNT_PATH - Storage directory for generated DOCX files
  - Used in `server.py:29` - Railway volume persistence
  - Falls back to `./generated_docs` if not set

- RAILWAY_PUBLIC_DOMAIN or RAILWAY_STATIC_URL - Public URL for download links
  - Used in `server.py:371` - For Railway deployment
  - Generates absolute download URLs for generated documents

- PORT - HTTP server port (optional)
  - Default: 8000
  - Used in `run_http_server.py:33`

**Build:**
- No build config detected - Uses setuptools via `pyproject.toml`
- Entry point: `server:main` (script defined in `pyproject.toml:20`)

**Server Configuration:**
- `server_config.json` (optional, git-ignored)
  - Contains `public_url` for Ngrok/local deployment
  - Template provided in `server_config.json.sample`
  - Loaded in `server.py:380-382`
  - Priority: Environment variables override config file

## Platform Requirements

**Development:**
- Python 3.10+
- pip or uv package manager
- Virtual environment (.venv)

**Production:**
- Railway (recommended)
  - Volume mount support for persistent document storage
  - Environment variable support
  - Port forwarding (default 8000)

- Ngrok (for local/testing)
  - Public URL forwarding
  - Configured via `server_config.json`

- Any platform supporting Python 3.10 + uvicorn
  - Linux container environments
  - Cloud platforms (Railway, Heroku, etc.)

**Deployment:**
- Procfile present for Heroku/Railway: `web: python run_http_server.py --host 0.0.0.0`
- HTTP port requirement: TCP port 8000 (or custom via PORT env var)
- Storage requirement: Persistent volume for 24-hour document retention
  - Default 10MB max file size limit (enforced in `fetch_extra_info()`)

---

*Stack analysis: 2026-02-15*
