---
phase: 02-mcp-tool-integration-file-management
plan: 01
subsystem: api
tags: [mcp, pdf, reportlab, pydantic, fastmcp, citation-reporting]

# Dependency graph
requires:
  - phase: 01-pdf-infrastructure-data-model
    provides: citation_schema.py with validate_citation_json, pdf_generator.py with generate_source_report_pdf, DejaVu Sans font setup
provides:
  - generate_source_report MCP tool in server.py
  - PDF file lifecycle management (cleanup thread handles .pdf files)
  - Download endpoint serves PDF files with correct Content-Type
affects: [03-citation-features-workflow, mcp-tool-testing, railway-deployment]

# Tech tracking
tech-stack:
  added: []
  patterns: [MCP tool pattern for PDF generation mirroring generate_compliance_doc, unified file cleanup for multiple extensions]

key-files:
  created: []
  modified: [server.py]

key-decisions:
  - "Use _sources_ infix in PDF filename to distinguish from compliance docs ({ModelName}_sources_{uuid}.pdf)"
  - "Use standard base64.b64encode (not urlsafe_b64encode) for MCP EmbeddedResource to avoid validation errors"
  - "Extend cleanup_old_files using tuple form of endswith(('.docx', '.pdf')) for unified lifecycle management"

patterns-established:
  - "MCP tool pattern: validate input → generate to BytesIO → save to DATA_DIR → base64 encode → return [TextContent, EmbeddedResource]"
  - "Railway URL construction: check RAILWAY_PUBLIC_DOMAIN/RAILWAY_STATIC_URL env vars, prepend https:// if missing scheme, fallback to server_config.json"

# Metrics
duration: 2min
completed: 2026-02-15
---

# Phase 2 Plan 1: MCP Tool Integration & File Management Summary

**Generate source citation PDF reports through MCP tool with 24-hour file lifecycle using ReportLab and Pydantic validation**

## Performance

- **Duration:** 2 minutes
- **Started:** 2026-02-15T13:36:11Z
- **Completed:** 2026-02-15T13:39:00Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- MCP tool `generate_source_report` accepts citation JSON, validates with Pydantic schema, generates PDF, returns download link + embedded base64
- PDF files automatically deleted after 24 hours alongside DOCX files
- Download endpoint serves PDF files with correct application/pdf Content-Type via FileResponse auto-detection

## Task Commits

Each task was committed atomically:

1. **Task 1: Create generate_source_report MCP tool** - `abc23e2` (feat)
2. **Task 2: Extend cleanup thread to handle .pdf files** - `abc23e2` (feat)

_Note: Both tasks committed together in single commit as they are tightly coupled (both handle PDF file lifecycle)_

## Files Created/Modified
- `server.py` - Added generate_source_report MCP tool with @mcp.tool() decorator, imports from citation_schema and pdf_generator, extended cleanup_old_files to handle .pdf files

## Decisions Made

**Use standard base64 encoding instead of urlsafe:**
- Plan specified NOT to use urlsafe_b64encode based on research findings
- MCP validation errors occur with urlsafe encoding
- Used `base64.b64encode(pdf_bytes).decode('utf-8')` matching generate_compliance_doc pattern

**Filename pattern distinguishes PDF types:**
- Compliance docs: `{ModelName}_{uuid}.docx`
- Source reports: `{ModelName}_sources_{uuid}.pdf`
- The `_sources_` infix makes file purpose clear in DATA_DIR listings

**Unified cleanup implementation:**
- Changed `filename.endswith(".docx")` to `filename.endswith((".docx", ".pdf"))`
- Tuple form of endswith() is idiomatic Python for multiple extension checks
- Single cleanup thread handles all generated document types with same 24-hour TTL

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. All verification checks passed:
- Tool imports successfully
- Valid JSON produces list with TextContent + EmbeddedResource
- Invalid JSON produces list with TextContent containing "Validation Error"
- Error paths always return lists (never bare TextContent)
- Cleanup function handles both .docx and .pdf extensions
- FileResponse auto-detects application/pdf MIME type for .pdf files
- All 27 existing tests still pass
- Integration test verifies end-to-end flow: JSON → PDF → file saved → download link → cleanup

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Ready for Phase 2 Plan 2 (additional MCP tool integration or file management features) and Phase 3 (citation features and workflow).

The core integration is complete:
- Phase 1 infrastructure (citation_schema.py, pdf_generator.py) successfully connected to MCP server
- Users can call `generate_source_report` tool with citation JSON
- PDF generation follows same patterns as existing generate_compliance_doc tool
- File lifecycle management (save, serve, cleanup) works identically for PDF and DOCX

No blockers or concerns for continuing with Phase 2 or Phase 3.

## Self-Check: PASSED

Verified claims:
- FOUND: server.py (modified file exists)
- FOUND: abc23e2 (commit exists in git history)

---
*Phase: 02-mcp-tool-integration-file-management*
*Completed: 2026-02-15*
