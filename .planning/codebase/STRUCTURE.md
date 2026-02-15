# Codebase Structure

**Analysis Date:** 2026-02-15

## Directory Layout

```
ai_act_compliance_mcp_server/
├── server.py                    # Main MCP server with tools, resources, routes
├── run_http_server.py           # HTTP/CORS wrapper for Railway deployment
├── docx_generator.py            # Document template filling logic
├── questions.json               # 50+ EU AI Act compliance questions schema
├── context.md                   # Custom LLM instructions for compliance workflow
├── server_config.json           # Public URL config (Ngrok/local)
├── pyproject.toml               # Project metadata and dependencies
├── requirements.txt             # Pinned Python dependencies
├── Procfile                     # Railway deployment command
├── runtime.txt                  # Python version specification
├── README.md                    # User documentation
├── MAPPING_GUIDE.md             # Placeholders for Word template customization
├── templates/                   # Word document templates
│   └── default_template.docx    # EU AI Act compliance form template
├── images/                      # Documentation images
│   └── demo_screenshot.png      # Screenshot for README
└── generated_docs/              # Runtime: Generated .docx files (with TTL cleanup)
```

## Directory Purposes

**Project Root:**
- Purpose: Contains all source code, configuration, and deployment files
- Contains: Python modules, config files, static assets
- Key files: `server.py` (entry point), `requirements.txt` (dependencies)

**templates/:**
- Purpose: Stores Word document templates for compliance form generation
- Contains: `.docx` template files with placeholders
- Key files: `default_template.docx` (loaded by `generate_compliance_doc` tool)
- Generated: No
- Committed: Yes

**images/:**
- Purpose: Documentation and README assets
- Contains: PNG/JPG screenshots
- Key files: `demo_screenshot.png` (referenced in README.md)
- Generated: No
- Committed: Yes

**generated_docs/:**
- Purpose: Runtime storage for generated compliance documents
- Contains: `.docx` files created by `generate_compliance_doc` tool
- Generated: Yes (at runtime when documents are generated)
- Committed: No (git-ignored)
- Cleanup: Automatic daemon thread deletes files >24 hours old

**.venv/:**
- Purpose: Python virtual environment
- Contains: Installed packages, interpreter
- Generated: Yes (created by `uv sync` or `pip install`)
- Committed: No (git-ignored)

**.planning/codebase/:**
- Purpose: GSD codebase analysis documents
- Contains: ARCHITECTURE.md, STRUCTURE.md, CONVENTIONS.md, TESTING.md, CONCERNS.md
- Generated: Yes (by mapping tools)
- Committed: Yes

## Key File Locations

**Entry Points:**

- `server.py`: Main FastMCP server initialization and tool definitions. Instantiates FastMCP, registers three tools (`fetch_hf_model_card`, `get_compliance_requirements`, `generate_compliance_doc`) and two resources, defines custom HTTP routes. Run via `fastmcp run server.py` (stdio) or imported by `run_http_server.py` (HTTP).

- `run_http_server.py`: HTTP wrapper for Railway/cloud deployment. Converts FastMCP stdio server to Starlette HTTP app, patches /mcp route for POST support, adds CORS middleware, starts Uvicorn on port 8000 (or PORT env var).

**Configuration:**

- `server_config.json`: Stores public URL for download links. Fallback source when Railway env vars not set. Format: `{"public_url": "https://your-domain.com"}`. Used by `generate_compliance_doc` when constructing file download URLs.

- `context.md`: Custom instructions injected into Claude's reasoning. Specifies workflow (don't interview users, require specific model IDs, infer reasonable defaults). Read by `get_compliance_context()` resource and Claude loads it automatically.

- `pyproject.toml`: Python project metadata, dependencies, and build config. Specifies Python >=3.10, lists core deps: mcp[cli], huggingface_hub, python-docx.

- `requirements.txt`: Pinned versions of all dependencies (97 packages including fastmcp, huggingface_hub, python-docx, requests, pypdf).

- `Procfile`: Single line: `python run_http_server.py`. Tells Railway how to start the application.

- `runtime.txt`: Python version string (e.g., `python-3.10.0`). Used by Railway to select runtime.

**Core Logic:**

- `server.py`: 492 lines containing:
  - FastMCP instance creation with security settings (line 21-22)
  - Storage configuration with Railway volume support (line 27-37)
  - Background cleanup daemon thread (line 40-70)
  - External content fetching with retry logic (line 73-157)
  - Model card enrichment with link filtering (line 159-216)
  - Tool: `fetch_hf_model_card()` (line 218-247)
  - Tool: `get_compliance_requirements()` (line 249-282)
  - Tool: `generate_compliance_doc()` (line 322-421)
  - Resource: `compliance-questions://` (line 424-469)
  - Resource: `compliance-context://` (line 471-482)
  - Custom route: `/download/{filename}` GET (line 284-302)
  - Custom route: `/sse` OPTIONS/POST (line 304-320)

- `docx_generator.py`: 62 lines containing:
  - `load_docx_from_template(path_or_file)`: Loads .docx file (line 6-10)
  - `process_tables(tables, display_data)`: Recursively processes nested tables for placeholder substitution (line 12-28)
  - `fill_template(template_path, output_path, data)`: Main entry point, converts yes/no to checkboxes, substitutes all `{{key}}` placeholders in paragraphs and tables (line 30-59)

**Data & Schema:**

- `questions.json`: 25KB JSON array of 50+ compliance question objects. Each contains `id` (field identifier), `question` (prompt), `description` (guidance). Examples: `date_last_updated`, `model_architecture`, `input_modalities_text_check`. Used by tools to instruct Claude on what to answer.

**Templates:**

- `templates/default_template.docx`: Word document template with `{{placeholder}}` syntax for field substitution. Follows EU AI Act Article 53 structure. Loaded and filled by `docx_generator.fill_template()`.

## Naming Conventions

**Files:**

- Modules: lowercase with underscores (`server.py`, `docx_generator.py`, `run_http_server.py`)
- Configuration: lowercase with underscores or standard names (`context.md`, `server_config.json`, `questions.json`, `pyproject.toml`)
- Generated documents: Format `{model_name}_{uuid}.docx` (e.g., `Llama_3_2_1B_a1b2c3.docx`) - see line 349-351 in `server.py`
- Deployment: `Procfile`, `runtime.txt` (standard names)

**Directories:**

- Standard: `templates/`, `images/`, `generated_docs/` (lowercase, plural, descriptive)
- Hidden: `.venv/`, `.git/`, `.planning/` (lowercase, dot-prefix)

**Functions:**

- camelCase preferred: `fetch_hf_model_card()`, `extract_and_enrich_model_card()`, `fill_template()`, `process_tables()`, `cleanup_old_files()`
- Tool decorators: All lowercase with underscores (`@mcp.tool()`, `@mcp.resource()`)

**Variables:**

- Constants: UPPERCASE with underscores (`MAX_FETCHES`, `DATA_DIR`, `RAILWAY_VOLUME`)
- Local variables: snake_case (`model_id`, `enrichment_text`, `doc_bytes`)

**JSON Fields:**

- questions.json keys: snake_case (`model_name`, `input_modalities_text_check`, `design_specs`)
- Compliance data: Mirrors question IDs in snake_case

## Where to Add New Code

**New Compliance Tool:**
- Primary code: `server.py` - Add new `@mcp.tool()` decorated function after existing tools (line 322+)
- Implementation pattern: Accept string parameters, return string or list[TextContent|EmbeddedResource], catch exceptions and return error messages
- Registration: Automatic via decorator

**New Data Enrichment Source:**
- Modify: `extract_and_enrich_model_card()` in `server.py` (line 159)
- Add relevant keyword to `relevant_keywords` list (line 175-178) or `skip_keywords` list (line 181-185)
- Extend `fetch_extra_info()` to handle new content type (add case after line 101-143)

**New Template:**
- Create: `.docx` file with `{{placeholder}}` syntax using Word
- Place: `templates/` directory with descriptive name (e.g., `template_gpai_article53.docx`)
- Reference: Update `generate_compliance_doc()` if multiple templates needed (currently hardcoded to `default_template.docx` on line 334)

**New Compliance Questions:**
- Edit: `questions.json` - Add object to root array with `id`, `question`, `description`
- ID pattern: Use snake_case, prefix with domain (e.g., `output_modalities_video_check`)
- Do not modify existing IDs (breaks backward compatibility with filled forms)

**Custom Context/Instructions:**
- Edit: `context.md` - This text is loaded by `get_compliance_context()` resource and available to Claude
- Affects: LLM behavior during compliance workflow
- Usage: Mention specific requirements or workflow changes

**Storage Configuration:**
- Edit: `server_config.json` for `public_url` (Ngrok, local)
- Or set environment variables for Railway deployment:
  - `RAILWAY_VOLUME_MOUNT_PATH` - Override storage directory
  - `RAILWAY_PUBLIC_DOMAIN` or `RAILWAY_STATIC_URL` - Base URL for download links

**New Custom HTTP Route:**
- Add in: `server.py` using `@mcp.custom_route(path, methods=[...])` decorator
- Example patterns: Line 284 (GET file download), Line 304-320 (OPTIONS/POST for CORS)
- Responsibilities: Return Response objects (from starlette.responses)

## Special Directories

**generated_docs/:**
- Purpose: Runtime storage for generated .docx files
- Created: Automatically at startup if missing (`os.makedirs(DATA_DIR, exist_ok=True)` on line 36)
- Generated: Yes - populated by `generate_compliance_doc()` tool
- Committed: No - listed in .gitignore
- Cleanup: Daemon thread deletes files >24 hours old (line 40-70, runs every 1 hour)
- Railway override: Can be mounted to persistent volume via environment variable `RAILWAY_VOLUME_MOUNT_PATH`

**templates/:**
- Purpose: Stores reusable Word document templates
- Generated: No - manually created Word files
- Committed: Yes - version controlled
- Access: Loaded by `generate_compliance_doc()` from `templates/default_template.docx`
- Customization: Edit in Word, use placeholders `{{field_id}}` matching questions.json ids, save as .docx (binary format, not text)

---

*Structure analysis: 2026-02-15*
