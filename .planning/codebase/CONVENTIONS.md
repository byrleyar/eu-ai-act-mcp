# Coding Conventions

**Analysis Date:** 2026-02-15

## Naming Patterns

**Files:**
- `snake_case.py` format used throughout codebase
- Purpose-driven names: `server.py`, `docx_generator.py`, `run_http_server.py`
- Temporary/utility files use descriptive names: `server_config.json`, `questions.json`

**Functions:**
- `snake_case` for all functions
- Descriptive action verbs at start: `fetch_extra_info()`, `fetch_hf_model_card()`, `cleanup_old_files()`, `extract_and_enrich_model_card()`
- Helper functions use `_` prefix or descriptive naming: `load_docx_from_template()`, `process_tables()`, `fill_template()`
- Boolean test functions use `is_` prefix: `is_relevant`, `is_garbage`, `is_pdf`

**Variables:**
- `snake_case` for all variable names
- Constants use `UPPER_SNAKE_CASE`: `DATA_DIR`, `MAX_FETCHES`, `RAILWAY_VOLUME`
- Counters/flags: `fetch_count`, `random_suffix`, `content_length`
- Data containers: `display_data`, `compliance_data`, `extra_info`, `enrichment_text`
- Descriptive names for temporary values: `source_summary`, `safe_name`, `short_name`

**Types:**
- Return type annotations used consistently: `-> str`, `-> Document`, `-> tuple[str, list[str]]`, `-> list[types.TextContent | types.EmbeddedResource]`
- Parameter type annotations used in main functions
- Union types use modern syntax: `list[types.TextContent | types.EmbeddedResource]` (Python 3.10+)
- Dict annotations: `data: dict`, `display_data: dict`

## Code Style

**Formatting:**
- No explicit formatter configured (Black/autopep8 not detected)
- Line length: varies, some lines exceed 100 characters (see lines 165-169, 241 in `server.py`)
- Indentation: 4 spaces consistently used
- String quotes: Double quotes preferred throughout

**Linting:**
- No linter configuration detected (pylint, flake8, ruff not configured)
- No `.flake8`, `.pylintrc`, or similar files present
- Code follows basic PEP 8 conventions but not strictly enforced

**Import Organization:**
```python
# Order observed in server.py:
1. Third-party library imports (mcp, huggingface_hub)
2. Standard library imports (os, json, time, threading, io, etc)
3. Local module imports (docx_generator, starlette)
```

See `server.py` lines 1-25 for actual import pattern.

**Path Aliases:**
- No path aliases or import paths configured
- Direct relative imports used: `from docx_generator import fill_template`
- Absolute third-party imports: `from mcp.server.fastmcp import FastMCP`

## Error Handling

**Patterns:**
- Broad `except Exception as e:` used throughout (lines 45, 62, 85, 111, 153, etc in `server.py`)
- Specific exception handling for known errors:
  - `except (RepositoryNotFoundError, EntryNotFoundError) as e:` - line 244, `server.py`
  - `except json.JSONDecodeError as e:` - line 341, `server.py`
  - `except FileNotFoundError:` - lines 466, 479, `server.py`
- Nested try/except blocks used for complex operations (lines 45-66, 107-112 in `server.py`)
- Error messages returned as strings or logged to console via `print()`
- Silent failure pattern used in some cases: `except Exception: pass` - line 142, `server.py`

**Return approach:**
```python
# Return error messages as strings to caller
except Exception as e:
    return f"Error: {str(e)}"

# Return wrapped in response objects (MCP tools)
except Exception as e:
    return [types.TextContent(type="text", text=f"Error: {str(e)}")]
```

## Logging

**Framework:**
- `print()` statements used exclusively for logging
- No structured logging library (logging module, loguru) detected

**Patterns:**
```python
# INFO level messages
print(f"INFO: Using storage directory: {DATA_DIR}")  # line 37

# DEBUG level messages
print(f"DEBUG: Converted Arxiv abstract link to PDF: {url}")  # line 82
print(f"DEBUG: Attempting to fetch extra info from {url}")  # line 84

# Error/warning level
print(f"CLEANUP ERROR: Could not delete {filename}: {e}")  # line 61
print(f"WARNING: server.py was run directly!...")  # line 488
```

- Prefix pattern: `[LEVEL]: message` or `PREFIX: message`
- Used in cleanup thread for status: `print(f"CLEANUP: Deleted expired file {filename}")`

## Comments

**When to Comment:**
- Used to explain non-obvious logic or special handling
- Marks important configuration sections: `# --- storage configuration ---`, `# --- background cleanup task ---`
- Used to explain branching decisions: `# DECISION LOGIC:`, `# CASE 1: PDF`, `# CASE 2: Hugging Face Model Card`
- Single-line comments use `#` with space: `# Load template safely`

**JSDoc/TSDoc:**
- Docstrings used for all public functions and tools
- Docstring format uses triple quotes (Python style)
- Example from `server.py` line 219-222:
```python
def fetch_hf_model_card(model_id: str) -> str:
    """
    Fetches the raw text/markdown of a model card from HuggingFace.
    Automatically follows 1-2 important links (like Arxiv papers or linked model cards) to gather more context.
    Returns the content with a header explicitly listing the sources used.
    """
```

## Function Design

**Size:**
- Most functions 20-50 lines
- Larger functions: `fetch_extra_info()` (85 lines), `extract_and_enrich_model_card()` (58 lines)
- Thread function `cleanup_old_files()` designed as infinite loop (66 lines total including infinite loop and sleep)

**Parameters:**
- Functions take 1-3 parameters
- Type annotations required for all parameters
- Single responsibility: each function does one clear thing
- Examples: `fetch_extra_info(url: str)`, `fill_template(template_path, output_path, data: dict)`

**Return Values:**
- Type annotations on all public/tool functions
- Functions return either:
  - Simple types: `str`, `tuple[str, list[str]]`
  - Complex types: `list[types.TextContent | types.EmbeddedResource]`
  - List of objects: `list[types.TextContent]`

## Module Design

**Exports:**
- `server.py`: Exports `mcp` object (FastMCP instance) used by `run_http_server.py`
- `docx_generator.py`: Exports `fill_template()` function used by `server.py`
- Public functions marked with `@mcp.tool()` or `@mcp.resource()` decorators

**Barrel Files:**
- Not used in this project (no `__init__.py` files detected)
- Simple three-file structure: `server.py`, `docx_generator.py`, `run_http_server.py`

**Decoration Patterns:**
- `@mcp.tool()` - decorator for MCP tools exposed to clients (lines 218, 249, 322)
- `@mcp.custom_route()` - decorator for HTTP routes (lines 284, 304, 315)
- `@mcp.resource()` - decorator for MCP resources (lines 424, 471)

## Special Patterns

**String Formatting:**
- f-strings used throughout (modern Python 3.6+)
- Examples: `f"INFO: Using storage directory: {DATA_DIR}"`
- Nested braces for literal braces in output: `f"{{{{{key}}}}}"`  (line 22, `docx_generator.py`)

**Threading:**
- Background daemon thread for cleanup: `threading.Thread(target=cleanup_old_files, daemon=True)` (line 69, `server.py`)
- Infinite loop with sleep pattern (lines 44-66)

**Conditional Expressions:**
- Ternary operators used in specific contexts
- Multi-line if/elif/else for complex logic (lines 202-211, `server.py`)

---

*Convention analysis: 2026-02-15*
