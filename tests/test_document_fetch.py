import pytest
from unittest.mock import patch, MagicMock
from compliance_service import ComplianceService as _CS
_svc = _CS()
is_safe_url = _svc.is_safe_url
transform_arxiv_url = _svc.transform_arxiv_url
from server import fetch_external_document

def test_is_safe_url():
    """Verify URL safety validator."""
    assert is_safe_url("https://huggingface.co/docs") is True
    assert is_safe_url("http://arxiv.org/pdf/123.456") is True
    
    # Unsafe/Prohibited
    assert is_safe_url("http://localhost:8000") is False
    assert is_safe_url("http://127.0.0.1") is False
    assert is_safe_url("http://192.168.1.1") is False
    assert is_safe_url("http://10.0.0.1") is False
    assert is_safe_url("ftp://example.com") is False
    assert is_safe_url("file:///etc/passwd") is False

def test_transform_arxiv_url():
    """Verify arXiv URL transformation."""
    assert transform_arxiv_url("https://arxiv.org/abs/2401.12345") == "https://arxiv.org/pdf/2401.12345.pdf"
    assert transform_arxiv_url("https://arxiv.org/pdf/2401.12345.pdf") == "https://arxiv.org/pdf/2401.12345.pdf"
    assert transform_arxiv_url("https://example.com/page") == "https://example.com/page"

@patch("compliance_service.requests.get")
def test_fetch_external_document_large_file(mock_get):
    """Verify tool rejects large files."""
    mock_response = MagicMock()
    mock_response.headers = {"Content-Length": "20000000"} # ~20MB
    mock_get.return_value = mock_response
    
    result = fetch_external_document("https://example.com/large.pdf")
    assert "too large" in result

@patch("compliance_service.requests.get")
@patch("compliance_service.PdfReader")
def test_fetch_external_document_pdf_success(mock_pdf_reader, mock_get):
    """Verify successful PDF fetch and extraction."""
    # Mock requests response
    mock_response = MagicMock()
    mock_response.headers = {"Content-Type": "application/pdf", "Content-Length": "1000"}
    mock_response.status_code = 200
    mock_get.return_value = mock_response
    
    # Mock PdfReader
    mock_reader_inst = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Extracted PDF text content"
    mock_reader_inst.pages = [mock_page]
    mock_pdf_reader.return_value = mock_reader_inst
    
    result = fetch_external_document("https://example.com/paper.pdf")
    assert "SOURCE: PDF Document" in result
    assert "Extracted PDF text content" in result

@patch("compliance_service.requests.get")
def test_fetch_external_document_html_success(mock_get):
    """Verify successful HTML fetch and extraction."""
    mock_response = MagicMock()
    mock_response.headers = {"Content-Type": "text/html", "Content-Length": "1000"}
    mock_response.text = "<html><body>Some web text</body></html>"
    mock_response.status_code = 200
    mock_get.return_value = mock_response
    
    result = fetch_external_document("https://example.com/docs")
    assert "SOURCE: Web Page" in result
    assert "Some web text" in result
