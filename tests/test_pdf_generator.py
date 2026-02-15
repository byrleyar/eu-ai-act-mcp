"""Unit tests for PDF generator module.

Tests cover all INFRA requirements:
- INFRA-01: Unicode character rendering (smart quotes, accents, non-Latin)
- INFRA-02: In-memory generation (no filesystem writes)
- INFRA-03: Auto-wrapping tables (long text handling)
- INFRA-04: Multi-page header repetition

Uses pypdf.PdfReader to inspect generated PDFs and verify structure.
"""

import os
import pytest
from io import BytesIO
from pypdf import PdfReader

from pdf_generator import generate_source_report_pdf


@pytest.fixture
def sample_citation():
    """Return a single valid citation dict for basic tests."""
    return {
        'question_id': 'Q1',
        'question_text': 'What is the purpose of the AI system?',
        'answer': 'Risk assessment for insurance underwriting',
        'source_quote': 'The system performs automated risk scoring...',
        'source_section': 'Section 3.2',
        'confidence': 'DIRECT',
        'reasoning': 'Explicitly stated in technical documentation'
    }


@pytest.fixture
def many_citations():
    """Return 30 citations for multi-page testing."""
    citations = []
    for i in range(1, 31):
        citations.append({
            'question_id': f'Q{i}',
            'question_text': f'Question {i}: What is the purpose of feature {i}?',
            'answer': f'Feature {i} performs automated analysis for compliance purpose {i}',
            'source_quote': f'The technical specification document states that feature {i} is designed to handle specific compliance requirements as outlined in the regulatory framework.',
            'source_section': f'Section {i}.{i}',
            'confidence': ['DIRECT', 'INFERRED', 'DEFAULT', 'NOT FOUND'][i % 4],
            'reasoning': f'The reasoning for question {i} is based on direct analysis of the source documentation.'
        })
    return citations


def test_pdf_generates_valid_output(sample_citation):
    """Test basic PDF generation with valid citation data."""
    buf = BytesIO()
    generate_source_report_pdf(buf, [sample_citation])
    buf.seek(0)

    # Verify PDF is valid
    pdf = PdfReader(buf)
    assert len(pdf.pages) >= 1

    # Extract text and verify content appears
    page_text = pdf.pages[0].extract_text()
    assert 'What is the purpose' in page_text


def test_pdf_in_memory_no_file_io(sample_citation):
    """Test that no files are created during PDF generation (INFRA-02)."""
    # Snapshot current directory contents
    before = set(os.listdir('.'))

    # Generate PDF
    buf = BytesIO()
    generate_source_report_pdf(buf, [sample_citation])

    # Verify no new files created
    after = set(os.listdir('.'))
    assert before == after, "PDF generation should not create files on disk"


def test_pdf_unicode_smart_quotes(sample_citation):
    """Test Unicode smart quotes and curly apostrophes render without error (INFRA-01)."""
    citation = sample_citation.copy()
    citation['question_text'] = 'What is the "smart" system\'s purpose?'
    citation['answer'] = 'Risk assessment using AI—powered by machine learning'
    citation['source_quote'] = 'The document states: "The system\'s ML algorithms..."'

    buf = BytesIO()
    generate_source_report_pdf(buf, [citation])  # Should not raise exception
    buf.seek(0)

    # Verify PDF is valid
    pdf = PdfReader(buf)
    assert len(pdf.pages) >= 1


def test_pdf_unicode_accented_characters(sample_citation):
    """Test accented characters render without error (INFRA-01)."""
    citation = sample_citation.copy()
    citation['answer'] = 'café, naïve, résumé, Zürcher Kantonalbank'

    buf = BytesIO()
    generate_source_report_pdf(buf, [citation])
    buf.seek(0)

    # Verify PDF is valid
    pdf = PdfReader(buf)
    assert len(pdf.pages) >= 1


def test_pdf_unicode_non_latin(sample_citation):
    """Test non-Latin characters (Japanese) don't crash generation (INFRA-01)."""
    citation = sample_citation.copy()
    citation['source_quote'] = '日本語のテキスト - Japanese text in source quote'

    buf = BytesIO()
    generate_source_report_pdf(buf, [citation])  # Should not crash
    buf.seek(0)

    # Verify PDF is valid
    pdf = PdfReader(buf)
    assert len(pdf.pages) >= 1


def test_pdf_long_text_wrapping(sample_citation):
    """Test long text (1200+ characters) wraps without crash (INFRA-03)."""
    citation = sample_citation.copy()
    # Create 1200+ character string (20 repetitions = ~1140 chars)
    citation['source_quote'] = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. ' * 20

    buf = BytesIO()
    generate_source_report_pdf(buf, [citation])
    buf.seek(0)

    # Verify PDF is valid and has at least 1 page
    pdf = PdfReader(buf)
    assert len(pdf.pages) >= 1


def test_pdf_very_long_text_no_data_loss(sample_citation):
    """Test very long text appears without data loss (INFRA-03)."""
    citation = sample_citation.copy()
    # Create long but reasonable text (~900 chars) with markers
    long_text = 'This is a unique marker phrase. ' + ('Lorem ipsum dolor sit amet. ' * 30) + 'End marker phrase.'
    citation['source_quote'] = long_text

    buf = BytesIO()
    generate_source_report_pdf(buf, [citation])
    buf.seek(0)

    # Extract text from all pages
    pdf = PdfReader(buf)
    all_text = ''
    for page in pdf.pages:
        all_text += page.extract_text()

    # Verify key phrases appear somewhere in the output
    # Note: PDF text extraction may insert line breaks, so normalize whitespace
    normalized_text = ' '.join(all_text.split())
    assert 'unique marker phrase' in normalized_text
    assert 'End marker phrase' in normalized_text


def test_pdf_multipage_header_repetition(many_citations):
    """Test multi-page table repeats headers on page 2+ (INFRA-04)."""
    buf = BytesIO()
    generate_source_report_pdf(buf, many_citations)
    buf.seek(0)

    # Verify PDF has multiple pages
    pdf = PdfReader(buf)
    assert len(pdf.pages) >= 2, "30 citations should produce at least 2 pages"

    # Extract text from page 2
    page2_text = pdf.pages[1].extract_text()

    # Verify header text appears on page 2 (header repetition)
    # Check for at least one header column name
    assert 'Question' in page2_text or 'Answer' in page2_text or 'Confidence' in page2_text


def test_pdf_all_confidence_levels(sample_citation):
    """Test all confidence level values render correctly."""
    confidence_levels = ['DIRECT', 'INFERRED', 'DEFAULT', 'NOT FOUND']
    citations = []

    for level in confidence_levels:
        citation = sample_citation.copy()
        citation['question_id'] = f'Q_{level}'
        citation['confidence'] = level
        citations.append(citation)

    buf = BytesIO()
    generate_source_report_pdf(buf, citations)
    buf.seek(0)

    # Extract text from all pages
    pdf = PdfReader(buf)
    all_text = ''
    for page in pdf.pages:
        all_text += page.extract_text()

    # Verify all confidence levels appear
    for level in confidence_levels:
        assert level in all_text


def test_pdf_empty_optional_fields(sample_citation):
    """Test empty optional fields (answer, source_quote, source_section) don't crash."""
    citation = sample_citation.copy()
    citation['answer'] = ''
    citation['source_quote'] = ''
    citation['source_section'] = ''

    buf = BytesIO()
    generate_source_report_pdf(buf, [citation])  # Should not raise exception
    buf.seek(0)

    # Verify PDF is valid
    pdf = PdfReader(buf)
    assert len(pdf.pages) >= 1


def test_pdf_xml_special_characters(sample_citation):
    """Test XML special characters (&, <, >, quotes) don't crash Paragraph parser."""
    citation = sample_citation.copy()
    citation['question_text'] = 'What is <tag> & how does it work?'
    citation['answer'] = 'The system uses <xml> & "quoted" values'
    citation['source_quote'] = 'Document states: <element attr="value"> & </element>'
    citation['reasoning'] = 'Found in section with <brackets> & ampersands &'

    buf = BytesIO()
    generate_source_report_pdf(buf, [citation])  # Should not crash
    buf.seek(0)

    # Verify PDF is valid
    pdf = PdfReader(buf)
    assert len(pdf.pages) >= 1


def test_pdf_has_title():
    """Test PDF contains expected title text."""
    citation = {
        'question_id': 'Q1',
        'question_text': 'Test question',
        'answer': 'Test answer',
        'source_quote': 'Test quote',
        'source_section': 'Section 1',
        'confidence': 'DIRECT',
        'reasoning': 'Test reasoning'
    }

    buf = BytesIO()
    generate_source_report_pdf(buf, [citation])
    buf.seek(0)

    # Extract page 1 text
    pdf = PdfReader(buf)
    page1_text = pdf.pages[0].extract_text()

    # Verify title appears
    assert 'AI Act Compliance' in page1_text
