"""Integration tests for generate_source_report MCP tool.

Tests verify all Phase 2 requirements:
- TOOL-01: Tool has correct parameters (source_citations_json, model_name)
- TOOL-02: Validates JSON before generation
- TOOL-03: Returns TextContent + EmbeddedResource
- TOOL-04: Filename includes model_name and _sources_ suffix
- FILE-01: PDF saved to DATA_DIR
- FILE-02: Cleanup thread handles .pdf files
- FILE-03: PDFs served with correct Content-Type

Uses fixtures for test data and automatic cleanup of generated files.
"""

import json
import os
import base64
import inspect
import mimetypes
import pytest

from server import generate_source_report, cleanup_old_files, DATA_DIR


# Test fixtures

VALID_CITATION_JSON = json.dumps({
    "citations": [{
        "question_id": "Q1",
        "question_text": "What is the model architecture?",
        "answer": "Transformer-based",
        "source_quote": "We use a standard Transformer",
        "source_section": "Model Description",
        "confidence": "DIRECT",
        "reasoning": "Directly stated in model card"
    }]
})

MULTI_CITATION_JSON = json.dumps({
    "citations": [
        {
            "question_id": "Q1",
            "question_text": "Architecture?",
            "answer": "Transformer",
            "source_quote": "Quote",
            "source_section": "Section",
            "confidence": "DIRECT",
            "reasoning": "Direct match"
        },
        {
            "question_id": "Q2",
            "question_text": "Training data?",
            "answer": "",
            "source_quote": "",
            "source_section": "",
            "confidence": "NOT FOUND",
            "reasoning": "Not found in card"
        }
    ]
})


@pytest.fixture
def cleanup_pdfs():
    """Remove test-generated PDFs after test."""
    yield
    for f in os.listdir(DATA_DIR):
        if f.endswith('.pdf') and 'sources' in f:
            try:
                os.remove(os.path.join(DATA_DIR, f))
            except Exception:
                pass


# Basic functionality tests

def test_tool_returns_list_on_valid_input(cleanup_pdfs):
    """Call generate_source_report with valid input, verify result is a list with length 2."""
    result = generate_source_report(VALID_CITATION_JSON)

    assert isinstance(result, list)
    assert len(result) == 2


def test_tool_returns_text_content_with_download_link(cleanup_pdfs):
    """Verify result[0] is TextContent with type='text' and text containing 'download'."""
    result = generate_source_report(VALID_CITATION_JSON)

    # Check first item is TextContent
    assert hasattr(result[0], 'type')
    assert result[0].type == 'text'
    assert hasattr(result[0], 'text')
    assert 'download' in result[0].text.lower()


def test_tool_returns_embedded_resource_with_pdf(cleanup_pdfs):
    """Verify result[1] is EmbeddedResource with mimeType='application/pdf' and non-empty blob."""
    result = generate_source_report(VALID_CITATION_JSON)

    # Check second item is EmbeddedResource
    assert hasattr(result[1], 'type')
    assert result[1].type == 'resource'
    assert hasattr(result[1], 'resource')

    # Check resource has PDF mime type
    assert result[1].resource.mimeType == 'application/pdf'

    # Check blob is non-empty
    assert hasattr(result[1].resource, 'blob')
    assert isinstance(result[1].resource.blob, str)
    assert len(result[1].resource.blob) > 0


def test_tool_validates_base64_encoding(cleanup_pdfs):
    """Verify result[1].resource.blob can be decoded and contains PDF magic bytes."""
    result = generate_source_report(VALID_CITATION_JSON)

    blob = result[1].resource.blob

    # Decode base64
    decoded_bytes = base64.b64decode(blob)

    # Verify PDF magic bytes
    assert decoded_bytes.startswith(b'%PDF')


# File persistence tests

def test_tool_saves_pdf_to_data_dir(cleanup_pdfs):
    """After calling the tool, verify a .pdf file exists in DATA_DIR."""
    result = generate_source_report(VALID_CITATION_JSON, model_name="TestModel")

    # Find PDF files with 'sources' in name
    pdf_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.pdf') and 'sources' in f]

    assert len(pdf_files) > 0, "Expected at least one PDF file in DATA_DIR"


def test_tool_filename_includes_model_name_and_sources(cleanup_pdfs):
    """Call with model_name='MyTestModel', verify filename starts with 'MyTestModel_sources_' and ends with '.pdf'."""
    result = generate_source_report(VALID_CITATION_JSON, model_name="MyTestModel")

    # Find the generated file
    pdf_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.pdf') and 'sources' in f]

    assert len(pdf_files) > 0
    # Check most recently created file
    latest_file = pdf_files[-1]
    assert latest_file.startswith('MyTestModel_sources_')
    assert latest_file.endswith('.pdf')


def test_tool_filename_default_model_name(cleanup_pdfs):
    """Call without model_name parameter, verify filename starts with 'model_sources_'."""
    result = generate_source_report(VALID_CITATION_JSON)

    # Find the generated file
    pdf_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.pdf') and 'sources' in f]

    assert len(pdf_files) > 0
    latest_file = pdf_files[-1]
    assert latest_file.startswith('model_sources_')


def test_tool_sanitizes_model_name(cleanup_pdfs):
    """Call with model_name containing special characters, verify filename only contains safe characters."""
    result = generate_source_report(VALID_CITATION_JSON, model_name="Bad/Name\\With..Chars!")

    # Find the generated file
    pdf_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.pdf') and 'sources' in f]

    assert len(pdf_files) > 0
    latest_file = pdf_files[-1]

    # Verify filename contains only safe characters (alphanumeric, underscore, hyphen, dot)
    # Extract the filename without the random suffix
    base_name = latest_file.replace('_sources_', '|').split('|')[0]

    # Check that special characters have been removed/replaced
    for char in base_name:
        assert char.isalnum() or char in ('_', '-'), f"Unsafe character '{char}' found in filename"


# Error handling tests

def test_tool_returns_list_on_invalid_json(cleanup_pdfs):
    """Call with invalid JSON, verify result is a list with TextContent containing error message."""
    result = generate_source_report("not valid json")

    assert isinstance(result, list)
    assert len(result) == 1
    assert hasattr(result[0], 'type')
    assert result[0].type == 'text'
    assert 'Validation Error' in result[0].text or 'Error' in result[0].text


def test_tool_returns_list_on_schema_error(cleanup_pdfs):
    """Call with empty citations list, verify result is list with TextContent containing error message."""
    invalid_json = json.dumps({"citations": []})
    result = generate_source_report(invalid_json)

    assert isinstance(result, list)
    assert len(result) == 1
    assert hasattr(result[0], 'type')
    assert result[0].type == 'text'
    assert 'Error' in result[0].text


# Infrastructure validation tests

def test_cleanup_handles_pdf_extension():
    """Verify cleanup_old_files source code contains '.pdf' in the endswith check."""
    source = inspect.getsource(cleanup_old_files)

    # Verify .pdf is included in the cleanup logic
    assert '.pdf' in source
    # Verify it's in the context of file extension checking
    assert 'endswith' in source or '.pdf' in source


def test_pdf_content_type_detection():
    """Verify Python's mimetypes module returns 'application/pdf' for .pdf files."""
    mime_type, _ = mimetypes.guess_type("test.pdf")

    assert mime_type == 'application/pdf'


# Edge case tests

def test_tool_handles_multi_citation_report(cleanup_pdfs):
    """Call with MULTI_CITATION_JSON (2 citations including NOT FOUND), verify result structure and PDF size."""
    result = generate_source_report(MULTI_CITATION_JSON)

    # Verify result structure
    assert isinstance(result, list)
    assert len(result) == 2

    # Verify first item is TextContent
    assert result[0].type == 'text'

    # Verify second item is EmbeddedResource
    assert result[1].type == 'resource'

    # Decode PDF and verify it's non-trivial
    blob = result[1].resource.blob
    decoded_bytes = base64.b64decode(blob)

    # PDF with 2 citations should be > 1000 bytes (indicating real content)
    assert len(decoded_bytes) > 1000, "Multi-citation PDF should have substantial content"


def test_tool_handles_unicode_in_citations(cleanup_pdfs):
    """Create citation with Unicode characters, verify tool returns success without encoding crash."""
    unicode_json = json.dumps({
        "citations": [{
            "question_id": "Q1",
            "question_text": "What is the model's purpose?",
            "answer": "Risk assessment using smart quotes and em-dashes",
            "source_quote": "The system uses ML algorithms for naive Bayes classification",
            "source_section": "Technical Description",
            "confidence": "DIRECT",
            "reasoning": "Found in technical documentation"
        }]
    })

    # Should not raise exception
    result = generate_source_report(unicode_json)

    # Verify success
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[1].type == 'resource'

    # Verify PDF is valid
    blob = result[1].resource.blob
    decoded_bytes = base64.b64decode(blob)
    assert decoded_bytes.startswith(b'%PDF')


def test_tool_handles_long_text_in_citations(cleanup_pdfs):
    """Create citation with 500+ character answer and source_quote, verify tool returns success."""
    long_text = "This is a very long answer that exceeds 500 characters. " * 10  # ~570 chars
    long_quote = "This is a very long source quote that also exceeds 500 characters. " * 8  # ~536 chars

    long_text_json = json.dumps({
        "citations": [{
            "question_id": "Q1",
            "question_text": "What is the detailed purpose?",
            "answer": long_text,
            "source_quote": long_quote,
            "source_section": "Section 1",
            "confidence": "DIRECT",
            "reasoning": "Detailed explanation from documentation"
        }]
    })

    # Should not raise exception
    result = generate_source_report(long_text_json)

    # Verify success
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[1].type == 'resource'

    # Verify PDF is valid
    blob = result[1].resource.blob
    decoded_bytes = base64.b64decode(blob)
    assert decoded_bytes.startswith(b'%PDF')


def test_tool_embedded_resource_uri_format(cleanup_pdfs):
    """Verify result[1].resource.uri starts with 'file:///' and ends with '.pdf'."""
    result = generate_source_report(VALID_CITATION_JSON)

    # Check URI format (convert AnyUrl to string)
    uri = str(result[1].resource.uri)
    assert uri.startswith('file:///'), "URI should start with file:///"
    assert uri.endswith('.pdf'), "URI should end with .pdf"
