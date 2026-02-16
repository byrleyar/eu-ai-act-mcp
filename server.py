from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
import os
import json
from huggingface_hub import ModelCard, list_repo_files
from huggingface_hub.utils import EntryNotFoundError, RepositoryNotFoundError
from docx_generator import fill_template
from citation_schema import validate_citation_json, validate_report_coverage
from pdf_generator import generate_source_report_pdf
from starlette.requests import Request
from starlette.responses import FileResponse, Response
import mcp.types as types
import io
import base64
import uuid
import requests
import re
import ipaddress
from urllib.parse import urlparse
from pypdf import PdfReader

import time
import threading

# Initialize FastMCP server with DNS Rebinding Protection DISABLED

# This fixes "Invalid Host Header" errors on Railway/Ngrok/Localhost without strict host updates
security_settings = TransportSecuritySettings(enable_dns_rebinding_protection=False)
mcp = FastMCP("EU AI Act Compliance Server", transport_security=security_settings)

# --- storage configuration ---
# Use Railway volume if available, else default to 'generated_docs' in current dir
RAILWAY_VOLUME = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH")
if RAILWAY_VOLUME:
    DATA_DIR = os.path.abspath(RAILWAY_VOLUME)
else:
    DATA_DIR = os.path.join(os.getcwd(), "generated_docs")

# Ensure it exists
os.makedirs(DATA_DIR, exist_ok=True)
print(f"INFO: Using storage directory: {DATA_DIR}")

# --- background cleanup task ---
def cleanup_old_files():
    """
    Background thread that runs once an hour to delete .docx and .pdf files older than 24h.
    """
    while True:
        try:
            now = time.time()
            retention_seconds = 24 * 3600 # 24 hours

            # List files in DATA_DIR
            if os.path.exists(DATA_DIR):
                for filename in os.listdir(DATA_DIR):
                    file_path = os.path.join(DATA_DIR, filename)
                    # Delete .docx and .pdf files
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

        # Sleep for 1 hour
        time.sleep(3600)

# Start cleanup thread as daemon
cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
cleanup_thread.start()


def is_safe_url(url: str) -> bool:
    """
    Validates that a URL is absolute, uses http/https, and does not point to private IPs.
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            return False
        if not parsed.netloc:
            return False
        
        # Prevent SSRF by blocking private IP ranges
        # Note: This is a basic check. In production, we might want to resolve DNS
        # and check the IP, but for this MCP server, we'll start with host checks.
        host = parsed.hostname
        if not host:
            return False
            
        # Common private/local patterns
        if host.lower() in ('localhost', '127.0.0.1', '0.0.0.0', '::1'):
            return False
            
        # Check if it's an IP and if so, if it's private
        try:
            ip = ipaddress.ip_address(host)
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                return False
        except ValueError:
            # Not an IP address, likely a domain name
            pass
            
        return True
    except Exception:
        return False


def transform_arxiv_url(url: str) -> str:
    """
    Converts arXiv abstract links to direct PDF links.
    """
    if "arxiv.org/abs/" in url:
        url = url.replace("arxiv.org/abs/", "arxiv.org/pdf/")
        if not url.endswith(".pdf"):
            url += ".pdf"
    return url


def discover_relevant_links(text: str, repo_id: str) -> list[dict]:
    """
    Scans model card text and repository for relevant technical documents.
    Returns a list of discovered links with context.
    """
    discovered = []
    
    # 1. Repo Files (PDFs)
    try:
        files = list_repo_files(repo_id)
        for f in files:
            if f.lower().endswith('.pdf'):
                # Construct absolute URL for HF file
                url = f"https://huggingface.co/{repo_id}/resolve/main/{f}"
                discovered.append({
                    "url": url,
                    "label": f"Repository File: {f}",
                    "type": "repository_file",
                    "context": "Found in repository file list"
                })
    except Exception as e:
        print(f"DEBUG: Failed to list repo files: {e}")

    # 2. Markdown/HTML Links
    # Regex for markdown links: [Label](URL)
    md_links = re.finditer(r"(?<!\!)\[([^\]]+)\]\((https?://[^\)]+)\)", text)
    for match in md_links:
        label, url = match.groups()
        start, end = match.span()
        # Capture context (100 chars before/after)
        context_start = max(0, start - 100)
        context_end = min(len(text), end + 100)
        context = text[context_start:context_end].replace('\n', ' ').strip()
        
        discovered.append({
            "url": url,
            "label": label,
            "type": "markdown_link",
            "context": context
        })

    # Regex for HTML links: <a href="URL">Label</a>
    html_links = re.finditer(r'<a\s+(?:[^>]*?\s+)?href="([^"]*)"[^>]*>(.*?)</a>', text, re.IGNORECASE | re.DOTALL)
    for match in html_links:
        url, label = match.groups()
        start, end = match.span()
        context_start = max(0, start - 100)
        context_end = min(len(text), end + 100)
        context = text[context_start:context_end].replace('\n', ' ').strip()
        
        discovered.append({
            "url": url,
            "label": label,
            "type": "html_link",
            "context": context
        })

    # 3. BibTeX / ArXiv extraction
    # Look for arxiv.org/abs/ or /pdf/ pattern in text generally if missed by link regex
    arxiv_matches = re.finditer(r'(https?://(?:www\.)?arxiv\.org/(?:abs|pdf)/\d+\.\d+)', text)
    for match in arxiv_matches:
        url = match.group(1)
        # Check if already added
        if any(d['url'] == url for d in discovered):
            continue
            
        start, end = match.span()
        context_start = max(0, start - 100)
        context_end = min(len(text), end + 100)
        context = text[context_start:context_end].replace('\n', ' ').strip()
        
        discovered.append({
            "url": url,
            "label": "ArXiv Paper",
            "type": "citation",
            "context": context
        })

    return discovered

@mcp.tool()
def fetch_hf_model_card(model_id: str) -> str:
    """
    Fetches the raw text/markdown of a model card from HuggingFace.
    Returns the content AND a checklist of discovered technical documents/links.
    Does NOT automatically fetch external content (use `fetch_external_document` for that).
    """
    try:
        card = ModelCard.load(model_id)
        original_text = card.text
        
        # Discover links without fetching
        links = discover_relevant_links(original_text, model_id)
        
        # Filter duplicates based on URL
        unique_links = {l['url']: l for l in links}.values()
        
        # Format the output
        links_json = json.dumps(list(unique_links), indent=2)
        
        full_response = f"""
{'='*40}
MODEL CARD CONTENT ({model_id}):
{'='*40}

{original_text}

{'='*40}
### DISCOVERED DOCUMENTS (Use `fetch_external_document` to retrieve relevant ones)
{'='*40}
{links_json}
"""
        return full_response
        
    except (RepositoryNotFoundError, EntryNotFoundError) as e:
        return f"Error: Model or model card not found for ID '{model_id}'. Details: {str(e)}"
    except Exception as e:
        return f"Error fetching model card: {str(e)}"


@mcp.tool()
def fetch_external_document(url: str) -> str:
    """
    Retrieves and extracts text from an external document (PDF or HTML).
    Use this to gather information from papers or technical reports discovered in the model card.
    """
    if not is_safe_url(url):
        return f"Error: URL '{url}' is unsafe or prohibited."

    # Handle arXiv conversion
    fetch_url = transform_arxiv_url(url)
    
    print(f"DEBUG: Attempting to fetch document from {fetch_url}")
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Compliance-Bot/1.0)"}
        # Stream to check size and content type first
        response = requests.get(fetch_url, stream=True, timeout=15, headers=headers)
        response.raise_for_status()
        
        content_type = response.headers.get("Content-Type", "").lower()
        content_length = int(response.headers.get("Content-Length", 0))
        
        # Max 10MB
        if content_length > 10 * 1024 * 1024:
            return f"Error: File at {url} is too large ({content_length} bytes). Max 10MB."
            
        extracted_text = ""
        source_type = "External Document"

        if "application/pdf" in content_type or fetch_url.lower().endswith(".pdf"):
            source_type = "PDF Document"
            f = io.BytesIO()
            # Read chunks to respect stream
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
            
            reader = PdfReader(f)
            # Limit to first 15 pages
            pages_text = []
            for i, page in enumerate(reader.pages):
                if i >= 15: break
                text = page.extract_text()
                if text:
                    pages_text.append(text)
            extracted_text = "\n".join(pages_text)
        else:
            # Assume HTML/Text
            source_type = "Web Page"
            # Limit to 50k chars for raw text
            extracted_text = response.text[:50000]
            if len(response.text) > 50000:
                extracted_text += "\n[... Content Truncated ...]"

        if not extracted_text.strip():
            return f"Error: Could not extract any text from {url}."

        # Format response
        full_response = f"""
{'='*20}
SOURCE: {source_type}
URL: {url}
{'='*20}

{extracted_text}
"""
        return full_response

    except Exception as e:
        print(f"DEBUG: Failed to fetch {url}: {e}")
        return f"Error fetching document from {url}: {str(e)}"


@mcp.tool()
def get_compliance_requirements() -> str:
    """
    Returns the official schema of questions (JSON) that must be answered to generate the compliance document.
    Call this AFTER fetching the model card to know what information to extract.
    """
    try:
        with open("questions.json", "r") as f:
            questions_json = f.read()
        
        return f"""
*** SYSTEM INSTRUCTION ***
You are the AI Act Compliance Officer.
BELOW is the exact JSON schema of questions you need to answer to generate the document.

YOUR TASK:
1.  Review the Model Card data you have.
2.  Map that data to the `id` fields in the JSON below.
3.  **STRICT RULE:** Do NOT infer, estimate, or guess information not explicitly stated in the model card.
    - If the model card says "Exact inference computation not specified", DO NOT estimate it based on architecture.
    - If information is missing, leave the field as an empty string.
4.  Call `generate_compliance_doc` IMMEDIATELY with the filled JSON.
5.  **AFTER** calling the tool, you must generate a final response to the user listing:
    - Questions you could not answer because the data was missing.
    - **The sources you used** to generate this information (copy the "SOURCES USED" section from the model card text).
    - **The Download Link** provided by the `generate_compliance_doc` tool output (Repeat this link VERBATIM).
    - A reminder to the user to review the output.

---
QUESTIONS SCHEMA:
{questions_json}
"""
    except Exception as e:
        return f"Error reading questions: {str(e)}"

@mcp.custom_route("/download/{filename}", methods=["GET"])
async def download_file(request: Request) -> Response:
    filename = request.path_params.get("filename")
    
    # Basic security check
    if ".." in filename or "/" in filename or "\\" in filename:
         return Response("Invalid filename", status_code=400)
         
    # Serve from DATA_DIR
    file_path = os.path.join(DATA_DIR, filename)
    
    # Ensure the resolved path is actually within DATA_DIR (extra safety)
    if not os.path.commonpath([os.path.abspath(file_path), DATA_DIR]) == DATA_DIR:
         return Response("Access denied", status_code=403)
         
    if not os.path.exists(file_path):
        return Response("File not found or expired", status_code=404)
        
    return FileResponse(file_path, filename=filename)

@mcp.custom_route("/sse", methods=["OPTIONS"])
async def handle_sse_options(request: Request) -> Response:
    """
    Manually handle CORS OPTIONS preflight for /sse.
    """
    response = Response(status_code=200)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

@mcp.custom_route("/sse", methods=["POST"])
async def handle_sse_post(request: Request) -> Response:
    """
    Handle POST probes to /sse to prevent 405 errors.
    """
    return Response("Use GET for SSE stream", status_code=200)

@mcp.tool()
def generate_compliance_doc(compliance_data_json: str) -> list[types.TextContent | types.EmbeddedResource]:
    """
    Takes a JSON string containing all the answers to the compliance questions and generates a formatted Docx.
    The JSON structure should be a dictionary where keys match the 'id' fields in questions.json.
    Returns the generated document as an embedded resource.
    """
    # ensure templates dir exists
    template_dir = os.path.join(os.getcwd(), "templates")
    os.makedirs(template_dir, exist_ok=True)

    # Use default template if user didn't specify one (conceptually)
    template_path = os.path.join(template_dir, "default_template.docx")

    if not os.path.exists(template_path):
        return [types.TextContent(type="text", text=f"Error: Template not found at {template_path}")]

    try:
        data = json.loads(compliance_data_json)
    except json.JSONDecodeError as e:
        return [types.TextContent(type="text", text=f"Error: Invalid JSON data provided. {str(e)}")]

    # Determine filename from model name if present, else default
    model_name = data.get("model_name", "compliance_doc")
    # Sanitize filename
    safe_name = "".join(x for x in model_name if x.isalnum() or x in (' ', '_', '-')).strip().replace(' ', '_')
    # Truncate to 30 chars max and add random suffix for uniqueness
    short_name = safe_name[:30]
    random_suffix = uuid.uuid4().hex[:6]
    output_filename = f"{short_name}_{random_suffix}.docx"

    try:
        # Generate into a memory buffer
        buffer = io.BytesIO()
        fill_template(template_path, buffer, data)
        doc_bytes = buffer.getvalue()

        # SAVE to DATA_DIR
        output_path = os.path.join(DATA_DIR, output_filename)
        with open(output_path, "wb") as f:
            f.write(doc_bytes)

        # Encode as base64 string
        doc_b64 = base64.b64encode(doc_bytes).decode('utf-8')

        # Load public URL from config OR Environment Variable (Railway)
        base_url = ""

        # Priority 1: Environment Variable (Railway/Cloud)
        railway_domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN") or os.environ.get("RAILWAY_STATIC_URL")
        if railway_domain:
            if not railway_domain.startswith("http"):
                 railway_domain = f"https://{railway_domain}"
            base_url = railway_domain.rstrip("/")

        # Priority 2: Config File
        if not base_url:
            try:
                with open("server_config.json", "r") as f:
                    config = json.load(f)
                    base_url = config.get("public_url", "").rstrip("/")
            except Exception:
                pass

        download_path = f"/download/{output_filename}"

        # Construct link
        if base_url:
             full_link = f"{base_url}{download_path}"
        else:
             # Fallback if config not set
             full_link = download_path

        return [
            types.TextContent(
                type="text",
                text=f"""*** SYSTEM INSTRUCTION: DO NOT SUMMARIZE ***
You MUST display the following text VERBATIM to the user.

SUCCESS: Compliance document generated.

DOWNLOAD LINK:
[Download Generated Document]({full_link})

NOTE: This link will be active for 24 hours.

*** MANDATORY NEXT STEP ***
You MUST now call the `generate_source_report` tool to provide the audit trail.
Do NOT respond to the user or ask for permission. Proceed immediately.

REPORT SCHEMA REMINDER:
{{
  "citations": [
    {{
      "question_id": "...",
      "question_text": "...",
      "answer": "...",
      "source_quote": "...",
      "source_section": "...",
      "confidence": "DIRECT | INFERRED | DEFAULT | NOT FOUND | HALLUCINATED",
      "reasoning": "..."
    }}
  ]
}}
"""
            ),
            types.EmbeddedResource(
                type="resource",
                resource=types.BlobResourceContents(
                    blob=doc_b64,
                    mimeType="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    uri=f"file:///{output_filename}"
                )
            )
        ]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error generating document: {str(e)}")]


@mcp.tool()
def generate_source_report(source_citations_json: str, model_name: str = "model", model_card_id: str = "unknown") -> list[types.TextContent | types.EmbeddedResource]:
    """
    Generate a PDF source citation report from validated JSON.

    Validates the citation JSON against the schema, generates a formatted PDF report
    showing each question's answer with its source, confidence level, and reasoning,
    then returns a download link and the embedded PDF.

    Args:
        source_citations_json: JSON string with a "citations" array of citation objects
        model_name: Optional model name for the filename (default: "model")
        model_card_id: Optional model card identifier for footer and summary (default: "unknown")

    Returns:
        List containing TextContent (download link) and EmbeddedResource (base64 PDF)
    """
    # Validate JSON
    try:
        report = validate_citation_json(source_citations_json)
        
        # Enforce coverage validation using questions.json
        try:
            with open("questions.json", "r") as f:
                questions = json.load(f)
            required_ids = [q['id'] for q in questions]
            validate_report_coverage(report, required_ids)
        except Exception as e:
            return [types.TextContent(type="text", text=f"Coverage Validation Error: {e}")]
            
    except ValueError as e:
        return [types.TextContent(type="text", text=f"Validation Error: {e}")]

    # Generate PDF
    try:
        buffer = io.BytesIO()
        generate_source_report_pdf(buffer, [c.model_dump() for c in report.citations], model_card_id=model_card_id)
        pdf_bytes = buffer.getvalue()
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error generating PDF: {str(e)}")]

    # Build filename
    safe_name = "".join(x for x in model_name if x.isalnum() or x in (' ', '_', '-')).strip().replace(' ', '_')
    short_name = safe_name[:30]
    random_suffix = uuid.uuid4().hex[:6]
    filename = f"{short_name}_sources_{random_suffix}.pdf"

    # Save to DATA_DIR
    output_path = os.path.join(DATA_DIR, filename)
    with open(output_path, "wb") as f:
        f.write(pdf_bytes)

    # Base64 encode
    pdf_b64 = base64.b64encode(pdf_bytes).decode('utf-8')

    # Build download URL
    base_url = ""

    # Priority 1: Environment Variable (Railway/Cloud)
    railway_domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN") or os.environ.get("RAILWAY_STATIC_URL")
    if railway_domain:
        if not railway_domain.startswith("http"):
            railway_domain = f"https://{railway_domain}"
        base_url = railway_domain.rstrip("/")

    # Priority 2: Config File
    if not base_url:
        try:
            with open("server_config.json", "r") as f:
                config = json.load(f)
                base_url = config.get("public_url", "").rstrip("/")
        except Exception:
            pass

    download_path = f"/download/{filename}"

    # Construct link
    if base_url:
        full_link = f"{base_url}{download_path}"
    else:
        # Fallback if config not set
        full_link = download_path

    return [
        types.TextContent(
            type="text",
            text=f"""SUCCESS: Source citation report generated.

DOWNLOAD LINK:
[Download Source Report]({full_link})

NOTE: This link will be active for 24 hours. After that, the file will be automatically deleted from the server.
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


@mcp.resource("compliance-questions://")
def get_compliance_questions() -> str:
    """
    Returns the list of questions the LLM needs to answer to fill the compliance form.
    Reads from local 'questions.json' file.
    """
    try:
        with open("questions.json", "r") as f:
            questions_json = f.read()
        
        # We wrap the questions in a strict system prompt to force the LLM to use the tool
        return f"""
*** SYSTEM INSTRUCTION: READ CAREFULLY ***

You are the AI Act Compliance Officer. Your job is to generate a compliance document using the `generate_compliance_doc` tool.

BELOW IS THE SCHEMA OF QUESTIONS YOU NEED TO ANSWER.

INSTRUCTIONS:
1.  Read the Model Card you just fetched.
2.  Map information from the Model Card to the `id` fields in the JSON below.
3.  **STRICT RULE:** Do NOT infer, estimate, or guess information not explicitly stated in the model card.
    - If the model card says "Exact inference computation not specified", DO NOT estimate it based on architecture.
    - If information is missing, leave text fields as an empty string. DO NOT explain why it is missing.
4.  **STYLE GUIDELINES:**
    - Write as if YOU are the model creator. Use strict assertive language (e.g., "The model uses..." or "We evaluated...").
    - **FORBIDDEN PHRASES:** Do NOT use phrases like "The model card says...", "According to the text...", "The document mentions...", or "Not disclosed in the model card".
    - If data is missing, just write "N/A". Do NOT write "The model card does not specify...".
5.  **IMMEDIATELY call the `generate_compliance_doc` tool** with your answers.
6.  **DO NOT** ask the user to answer these questions.
7.  **DO NOT** try to "build a form" or "create a questionnaire" in the chat.
8.  **DO NOT** look for other skills or files. The `generate_compliance_doc` tool IS the form builder.
9.  **AFTER** calling the tool, generate a final response to the user listing:
    - ANY questions you could not answer because the data was missing.
    - **The sources you used** (copy the "SOURCES USED" section from the model card text).
    - **The Download Link** provided by the tool output.

---
QUESTIONS SCHEMA:
{questions_json}
*** END INSTRUCTIONS ***
"""
    except FileNotFoundError:
        return "Error: questions.json not found"
    except Exception as e:
        return f"Error reading questions: {str(e)}"

@mcp.resource("compliance-context://")
def get_compliance_context() -> str:
    """
    Returns additional context provided by the user in 'context.md'.
    """
    try:
        with open("context.md", "r") as f:
            return f.read()
    except FileNotFoundError:
        return "No additional context provided."
    except Exception as e:
        return f"Error reading context: {str(e)}"



if __name__ == "__main__":
    # If this runs, it means the custom runner was NOT used.
    print("WARNING: server.py was run directly! This server uses default FastMCP settings.")
    print("If you are seeing '404' or '405' errors, you must use 'run_http_server.py' instead.")
    mcp.run()

