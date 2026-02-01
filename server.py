from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
import os
import json
from huggingface_hub import ModelCard
from huggingface_hub.utils import EntryNotFoundError, RepositoryNotFoundError
from docx_generator import fill_template
from starlette.requests import Request
from starlette.responses import FileResponse, Response
import mcp.types as types
import io
import base64
import uuid
import requests
import re
from pypdf import PdfReader

# Initialize FastMCP server with DNS Rebinding Protection DISABLED

# This fixes "Invalid Host Header" errors on Railway/Ngrok/Localhost without strict host updates
security_settings = TransportSecuritySettings(enable_dns_rebinding_protection=False)
mcp = FastMCP("EU AI Act Compliance Server", transport_security=security_settings)

import time
import threading

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
    Background thread that runs once an hour to delete files older than 24h.
    """
    while True:
        try:
            now = time.time()
            retention_seconds = 24 * 3600 # 24 hours
            
            # List files in DATA_DIR
            if os.path.exists(DATA_DIR):
                for filename in os.listdir(DATA_DIR):
                    file_path = os.path.join(DATA_DIR, filename)
                    # Only delete .docx files to be safe
                    if os.path.isfile(file_path) and filename.endswith(".docx"):
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


def fetch_extra_info(url: str) -> str:
    """
    Helper to fetch content from external URLs (PDFs or HF Model Cards).
    """
    # Special handling for Arxiv: Convert /abs/ to /pdf/
    if "arxiv.org/abs/" in url:
        url = url.replace("arxiv.org/abs/", "arxiv.org/pdf/")
        if not url.endswith(".pdf"):
            url += ".pdf"
        print(f"DEBUG: Converted Arxiv abstract link to PDF: {url}")

    print(f"DEBUG: Attempting to fetch extra info from {url}")
    try:
        # Stream request to check headers first
        headers = {"User-Agent": "Mozilla/5.0 (Compliance-Bot/1.0)"}
        response = requests.get(url, stream=True, timeout=10, headers=headers)
        response.raise_for_status()
        
        content_type = response.headers.get("Content-Type", "").lower()
        content_length = int(response.headers.get("Content-Length", 0))
        
        # Safety: Don't download huge files > 10MB
        if content_length > 10 * 1024 * 1024:
            return f"\n[Skipped link {url}: File too large ({content_length} bytes)]"
            
        extracted_text = ""
        source_type = "External Link"

        # CASE 1: PDF
        # Handle GitHub blob links by converting to raw
        if "github.com" in url and "/blob/" in url and url.lower().endswith(".pdf"):
             url = url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
             print(f"DEBUG: Converted GitHub blob link to raw: {url}")
             # Re-request with new URL
             try:
                 response = requests.get(url, stream=True, timeout=10, headers=headers)
                 response.raise_for_status()
                 content_type = response.headers.get("Content-Type", "").lower()
             except Exception as e:
                 return f"\n[Error fetching raw PDF from {url}: {e}]"

        if "application/pdf" in content_type or url.lower().endswith(".pdf"):
            source_type = "PDF Paper"
            f = io.BytesIO()
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
            
            reader = PdfReader(f)
            # Limit to first 15 pages to save context
            pages_text = []
            for i, page in enumerate(reader.pages):
                if i >= 15: break
                text = page.extract_text()
                if text:
                    pages_text.append(text)
            extracted_text = "\n".join(pages_text)

        # CASE 2: Hugging Face Model Card (recursion)
        elif "huggingface.co" in url and "resolve" not in url:
            # Attempt to pattern match a model ID
            # e.g. https://huggingface.co/mistralai/Mistral-7B-v0.1
            match = re.search(r"huggingface\.co/([^/]+/[^/]+)", url)
            if match:
                linked_model_id = match.group(1)
                # Avoid self-ref
                source_type = f"Linked Model Card ({linked_model_id})"
                try:
                    linked_card = ModelCard.load(linked_model_id)
                    extracted_text = linked_card.text
                except Exception:
                    pass

        if extracted_text:
            # Truncate to reasonable length (e.g. 12k chars)
            truncated_text = extracted_text[:12000]
            if len(extracted_text) > 12000:
                truncated_text += "\n[... Content Truncated ...]"
            
            return f"\n\n{'='*20}\nEXTRA CONTEXT FETCHED FROM: {source_type}\nURL: {url}\n{'='*20}\n{truncated_text}\n"

    except Exception as e:
        print(f"DEBUG: Failed to fetch {url}: {e}")
        return f"\n[Error fetching info from {url}: {str(e)}]"

    return ""

def extract_and_enrich_model_card(text: str) -> tuple[str, list[str]]:
    """
    Scans for relevant links in the model card and fetches their content.
    Returns a tuple of (enriched_text, list_of_sources).
    """
    # Regex for markdown links: [Label](URL)
    md_links = re.findall(r"(?<!\!)\[([^\]]+)\]\((https?://[^\)]+)\)", text)
    
    # Regex for HTML links: <a href="URL">Label</a>
    # Note: Capture groups are (URL, Label)
    html_links = re.findall(r'<a\s+(?:[^>]*?\s+)?href="([^"]*)"[^>]*>(.*?)</a>', text, re.IGNORECASE | re.DOTALL)
    
    # Normalize html links to (Label, URL) and combine
    all_links = md_links + [(label, url) for url, label in html_links]
    
    # Priority keywords that suggest high info density
    relevant_keywords = [
        "paper", "arxiv", "technical report", "model card", "whitepaper", 
        "specification", "datasheet", "documentation", "full details"
    ]
    
    # Negative keywords to skip waste
    skip_keywords = [
        "license", "bounty", "grant", "donation", "citation", "bibtex", 
        "join", "discord", "twitter", "community", "badge", "deploy",
        "colab", "demo"
    ]
    
    enrichment_text = ""
    fetched_urls = set()
    fetch_count = 0
    MAX_FETCHES = 2  # "one or two links down"
    
    for label, url in all_links:
        if fetch_count >= MAX_FETCHES:
            break
            
        if url in fetched_urls:
            continue
            
        label_lower = label.lower()
        url_lower = url.lower()
        
        # DECISION LOGIC:
        # 1. Must contain relevant keyword
        # 2. Must NOT contain skip keyword
        # 3. OR be a direct PDF link (very high signal)
        
        is_relevant = any(k in label_lower for k in relevant_keywords)
        is_garbage = any(k in label_lower for k in skip_keywords)
        is_pdf = url_lower.endswith(".pdf") or "arxiv.org/pdf" in url_lower
        
        if (is_relevant or is_pdf) and not is_garbage:
            fetched_urls.add(url)
            enrichment_text += fetch_extra_info(url)
            fetch_count += 1
            
    return enrichment_text, list(fetched_urls)

@mcp.tool()
def fetch_hf_model_card(model_id: str) -> str:
    """
    Fetches the raw text/markdown of a model card from HuggingFace.
    Automatically follows 1-2 important links (like Arxiv papers or linked model cards) to gather more context.
    Returns the content with a header explicitly listing the sources used.
    """
    try:
        card = ModelCard.load(model_id)
        original_text = card.text
        
        # Enrich the content by following relevant links
        extra_info, sources = extract_and_enrich_model_card(original_text)
        
        # Construct Source Summary
        if not sources:
            source_summary = f"SOURCES USED:\n1. Hugging Face Model Card for '{model_id}' (Primary)\n   - No additional relevant links found or followed."
        else:
            source_list = [f"1. Hugging Face Model Card for '{model_id}' (Primary)"]
            for i, src in enumerate(sources, 2):
                source_list.append(f"{i}. External Link: {src}")
            source_summary = "SOURCES USED:\n" + "\n".join(source_list)

        full_response = f"{source_summary}\n\n{'='*40}\nMODEL CARD CONTENT:\n{'='*40}\n\n{original_text}\n{extra_info}\n\n*** MODEL CARD FETCHED SUCCESFULLY ***\nNEXT STEP: Call the `get_compliance_requirements` tool to retrieve the list of questions you need to answer based on this text."
        return full_response
        
    except (RepositoryNotFoundError, EntryNotFoundError) as e:
        return f"Error: Model or model card not found for ID '{model_id}'. Details: {str(e)}"
    except Exception as e:
        return f"Error fetching model card: {str(e)}"

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
You MUST display the following text VERBATIM to the user. Do not call any other tools.

SUCCESS: Compliance document generated.

DOWNLOAD LINK:
[Download Generated Document]({full_link})

NOTE: This link will be active for 24 hours. After that, the file will be automatically deleted from the server.

(If the link above is not absolute, please configure `server_config.json` with your Ngrok URL)
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

