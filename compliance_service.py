import os
import json
import io
import base64
import uuid
import requests
import re
import ipaddress
import time
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse
from pydantic import BaseModel, Field
from huggingface_hub import ModelCard, list_repo_files
from huggingface_hub.utils import EntryNotFoundError, RepositoryNotFoundError
from pypdf import PdfReader

from docx_generator import fill_template
from citation_schema import validate_citation_json, validate_report_coverage
from pdf_generator import generate_source_report_pdf

class ProcessingContext(BaseModel):
    """Holds state for a single model processing run."""
    model_id: str
    output_path: str
    data_dir: str = Field(default="generated_docs")
    session_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    base_url: Optional[str] = None

class ComplianceService:
    """Core service for AI Act compliance report generation."""
    
    def __init__(self):
        # Could initialize shared resources here (e.g., sessions)
        pass

    def is_safe_url(self, url: str) -> bool:
        """Validates that a URL is absolute, uses http/https, and does not point to private IPs."""
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ('http', 'https'):
                return False
            if not parsed.netloc:
                return False
            
            host = parsed.hostname
            if not host:
                return False
                
            if host.lower() in ('localhost', '127.0.0.1', '0.0.0.0', '::1'):
                return False
                
            try:
                ip = ipaddress.ip_address(host)
                if ip.is_private or ip.is_loopback or ip.is_link_local:
                    return False
            except ValueError:
                pass
                
            return True
        except Exception:
            return False

    def transform_arxiv_url(self, url: str) -> str:
        """Converts arXiv abstract links to direct PDF links."""
        if "arxiv.org/abs/" in url:
            url = url.replace("arxiv.org/abs/", "arxiv.org/pdf/")
            if not url.endswith(".pdf"):
                url += ".pdf"
        return url

    def discover_relevant_links(self, text: str, repo_id: str) -> List[Dict[str, str]]:
        """Scans model card text and repository for relevant technical documents."""
        discovered = []
        
        # 1. Repo Files (PDFs)
        try:
            files = list_repo_files(repo_id)
            for f in files:
                if f.lower().endswith('.pdf'):
                    url = f"https://huggingface.co/{repo_id}/resolve/main/{f}"
                    discovered.append({
                        "url": url,
                        "label": f"Repository File: {f}",
                        "type": "repository_file",
                        "context": "Found in repository file list"
                    })
        except Exception:
            pass

        # 2. Markdown/HTML Links
        md_links = re.finditer(r"(?<!\!)\[([^\]]+)\]\((https?://[^\)]+)\)", text)
        for match in md_links:
            label, url = match.groups()
            start, end = match.span()
            context_start = max(0, start - 100)
            context_end = min(len(text), end + 100)
            context = text[context_start:context_end].replace('\n', ' ').strip()
            discovered.append({"url": url, "label": label, "type": "markdown_link", "context": context})

        html_links = re.finditer(r'<a\s+(?:[^>]*?\s+)?href="([^"]*)"[^>]*>(.*?)</a>', text, re.IGNORECASE | re.DOTALL)
        for match in html_links:
            url, label = match.groups()
            start, end = match.span()
            context_start = max(0, start - 100)
            context_end = min(len(text), end + 100)
            context = text[context_start:context_end].replace('\n', ' ').strip()
            discovered.append({"url": url, "label": label, "type": "html_link", "context": context})

        # 3. BibTeX / ArXiv extraction
        arxiv_matches = re.finditer(r'(https?://(?:www\.)?arxiv\.org/(?:abs|pdf)/\d+\.\d+)', text)
        for match in arxiv_matches:
            url = match.group(1)
            if any(d['url'] == url for d in discovered): continue
            start, end = match.span()
            context_start = max(0, start - 100)
            context_end = min(len(text), end + 100)
            context = text[context_start:context_end].replace('\n', ' ').strip()
            discovered.append({"url": url, "label": "ArXiv Paper", "type": "citation", "context": context})

        return discovered

    def fetch_hf_model_card(self, model_id: str) -> str:
        """Fetches the raw text/markdown of a model card from HuggingFace."""
        try:
            card = ModelCard.load(model_id)
            original_text = card.text
            links = self.discover_relevant_links(original_text, model_id)
            unique_links = {l['url']: l for l in links}.values()
            links_json = json.dumps(list(unique_links), indent=2)
            
            return f"""
{'='*40}
MODEL CARD CONTENT ({model_id}):
{'='*40}

{original_text}

{'='*40}
### DISCOVERED DOCUMENTS (Use `fetch_external_document` to retrieve relevant ones)
{'='*40}
{links_json}
"""
        except (RepositoryNotFoundError, EntryNotFoundError) as e:
            raise ValueError(f"Model or model card not found for ID '{model_id}'. {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Error fetching model card: {str(e)}")

    def fetch_external_document(self, url: str) -> str:
        """Retrieves and extracts text from an external document (PDF or HTML)."""
        if not self.is_safe_url(url):
            raise ValueError(f"URL '{url}' is unsafe or prohibited.")

        fetch_url = self.transform_arxiv_url(url)
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Compliance-Bot/1.0)"}
            response = requests.get(fetch_url, stream=True, timeout=15, headers=headers)
            response.raise_for_status()
            
            content_type = response.headers.get("Content-Type", "").lower()
            content_length = int(response.headers.get("Content-Length", 0))
            
            if content_length > 10 * 1024 * 1024:
                raise ValueError(f"File at {url} is too large. Max 10MB.")
                
            extracted_text = ""
            source_type = "External Document"

            if "application/pdf" in content_type or fetch_url.lower().endswith(".pdf"):
                source_type = "PDF Document"
                f = io.BytesIO()
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                
                reader = PdfReader(f)
                pages_text = []
                for i, page in enumerate(reader.pages):
                    if i >= 15: break
                    text = page.extract_text()
                    if text: pages_text.append(text)
                extracted_text = "\n".join(pages_text)
            else:
                source_type = "Web Page"
                extracted_text = response.text[:50000]
                if len(response.text) > 50000:
                    extracted_text += "\n[... Content Truncated ...]"

            if not extracted_text.strip():
                raise ValueError(f"Could not extract any text from {url}.")

            return f"\n{'='*20}\nSOURCE: {source_type}\nURL: {url}\n{'='*20}\n\n{extracted_text}"

        except Exception as e:
            raise RuntimeError(f"Error fetching document from {url}: {str(e)}")

    def generate_compliance_docx(self, ctx: ProcessingContext, compliance_data_json: str) -> Dict[str, Any]:
        """Generates a formatted Docx from compliance data."""
        template_dir = os.path.join(os.getcwd(), "templates")
        template_path = os.path.join(template_dir, "default_template.docx")

        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template not found at {template_path}")

        try:
            data = json.loads(compliance_data_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON data provided. {str(e)}")

        model_name = data.get("model_name", ctx.model_id.split("/")[-1])
        safe_name = "".join(x for x in model_name if x.isalnum() or x in (' ', '_', '-')).strip().replace(' ', '_')
        output_filename = f"{safe_name[:30]}_{ctx.session_id}.docx"
        output_path = os.path.join(ctx.data_dir, output_filename)

        os.makedirs(ctx.data_dir, exist_ok=True)

        try:
            buffer = io.BytesIO()
            fill_template(template_path, buffer, data)
            doc_bytes = buffer.getvalue()

            with open(output_path, "wb") as f:
                f.write(doc_bytes)

            doc_b64 = base64.b64encode(doc_bytes).decode('utf-8')
            download_url = f"{ctx.base_url}/download/{output_filename}" if ctx.base_url else f"/download/{output_filename}"

            return {
                "filename": output_filename,
                "path": output_path,
                "download_url": download_url,
                "doc_b64": doc_b64
            }
        except Exception as e:
            raise RuntimeError(f"Error generating document: {str(e)}")

    def generate_source_report_pdf(self, ctx: ProcessingContext, source_citations_json: str, model_card_id: str = "unknown") -> Dict[str, Any]:
        """Generates a PDF source citation report."""
        try:
            report = validate_citation_json(source_citations_json)
            
            # Enforce coverage validation
            with open("questions.json", "r") as f:
                questions = json.load(f)
            required_ids = [q['id'] for q in questions]
            validate_report_coverage(report, required_ids)
        except Exception as e:
            raise ValueError(f"Validation Error: {e}")

        try:
            buffer = io.BytesIO()
            generate_source_report_pdf(buffer, [c.model_dump() for c in report.citations], model_card_id=model_card_id)
            pdf_bytes = buffer.getvalue()
        except Exception as e:
            raise RuntimeError(f"Error generating PDF: {str(e)}")

        model_name = ctx.model_id.split("/")[-1]
        safe_name = "".join(x for x in model_name if x.isalnum() or x in (' ', '_', '-')).strip().replace(' ', '_')
        filename = f"{safe_name[:30]}_sources_{ctx.session_id}.pdf"
        output_path = os.path.join(ctx.data_dir, filename)

        os.makedirs(ctx.data_dir, exist_ok=True)

        with open(output_path, "wb") as f:
            f.write(pdf_bytes)

        pdf_b64 = base64.b64encode(pdf_bytes).decode('utf-8')
        download_url = f"{ctx.base_url}/download/{filename}" if ctx.base_url else f"/download/{filename}"

        return {
            "filename": filename,
            "path": output_path,
            "download_url": download_url,
            "pdf_b64": pdf_b64
        }
