# Phase 07 Research: Discovery Engine

## Objective
Improve link discovery in Hugging Face model cards to identify all relevant technical documentation, including repo files and citation-style links.

## Discovery Sources

### 1. Markdown & HTML Links
- Current regexes are okay but could be unified.
- **Improvement**: Capture ~100 characters before and after the link as "discovery context".

### 2. BibTeX & Citations
- Many model cards have a "Citation" section with LaTeX-style BibTeX.
- **Goal**: Extract `url`, `doi`, or `eprint` (arXiv) from these blocks.
- **Strategy**: Look for `@article`, `@misc`, etc., or common BibTeX fields.

### 3. Repository Files
- Hugging Face repositories often contain `.pdf` files (e.g., `technical_report.pdf`).
- **Tool**: `huggingface_hub.list_repo_files(repo_id)`.
- **Filtering**: Include any `.pdf` or `.docx` files found in the root or `docs/` folder.

## Metadata Structure
Each discovered link should return:
- `url`: The absolute URL or repo file path.
- `label`: The clickable text or filename.
- `type`: `paper`, `code`, `documentation`, `repository_file`.
- `context`: The text surrounding the link (for web links).

## Integration in `fetch_hf_model_card`
- The tool will no longer automatically fetch PDF content.
- Instead, it will append a `### DISCOVERED DOCUMENTS` section at the end of its response.
- This section will contain a JSON block that Claude can parse.

## Implementation Details
- Move discovery logic to a new function `discover_relevant_links(card_text, repo_id)`.
- Use `huggingface_hub` to list repo files.
- Refactor `fetch_hf_model_card` to return this new structured data.

## Verification
- Test with `meta-llama/Llama-3.1-8B-Instruct` (good BibTeX).
- Test with `MiniMaxAI/MiniMax-M2.5` (test repo file discovery).
