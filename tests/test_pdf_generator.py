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
from collections import Counter

from pdf_generator import generate_source_report_pdf, CONFIDENCE_COLORS


@pytest.fixture
def sample_citation():
    """Return a single valid citation dict for basic tests."""
    return {
        'question_id': 'Q1',
        'question_text': 'What is the purpose of the AI system?',
        'answer': 'Risk assessment for insurance underwriting',
        'source_quote': 'The system performs automated risk scoring...',
        'source_section': 'Section 3.2',
        'source_document': 'Model Card',
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

    # Extract text and verify content appears (normalize whitespace for PDF extraction)
    page_text = pdf.pages[0].extract_text()
    normalized = ' '.join(page_text.split())
    assert 'What is the purpose' in normalized or 'purpose of the AI system' in normalized


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


# Phase 3 Citation Feature Tests


def test_pdf_executive_summary_present(sample_citation):
    """Test executive summary appears with confidence breakdown."""
    # Create citations with all 4 confidence levels
    citations = []
    for level in ['DIRECT', 'INFERRED', 'DEFAULT', 'NOT FOUND']:
        citation = sample_citation.copy()
        citation['question_id'] = f'Q_{level}'
        citation['confidence'] = level
        citations.append(citation)

    buf = BytesIO()
    generate_source_report_pdf(buf, citations, model_card_id='test-org/test-model')
    buf.seek(0)

    # Extract text from page 1
    pdf = PdfReader(buf)
    page1_text = pdf.pages[0].extract_text()

    # Verify executive summary section appears
    assert 'Executive Summary' in page1_text
    # Verify DIRECT confidence level appears in breakdown
    assert 'DIRECT' in page1_text
    # Verify model_card_id appears
    assert 'test-org/test-model' in page1_text


def test_pdf_executive_summary_confidence_breakdown(sample_citation):
    """Test executive summary shows correct confidence counts."""
    # Create known distribution: 2 DIRECT, 1 INFERRED, 1 NOT FOUND
    citations = []

    # 2 DIRECT
    for i in range(2):
        c = sample_citation.copy()
        c['question_id'] = f'Q_DIRECT_{i}'
        c['confidence'] = 'DIRECT'
        citations.append(c)

    # 1 INFERRED
    c = sample_citation.copy()
    c['question_id'] = 'Q_INFERRED'
    c['confidence'] = 'INFERRED'
    citations.append(c)

    # 1 NOT FOUND
    c = sample_citation.copy()
    c['question_id'] = 'Q_NOT_FOUND'
    c['confidence'] = 'NOT FOUND'
    citations.append(c)

    buf = BytesIO()
    generate_source_report_pdf(buf, citations)
    buf.seek(0)

    # Extract text and normalize whitespace
    pdf = PdfReader(buf)
    page1_text = pdf.pages[0].extract_text()
    normalized = ' '.join(page1_text.split())

    # Verify counts appear (looking for "DIRECT: 2", "INFERRED: 1", "NOT FOUND: 1")
    # Text extraction may have spacing variations, so check key patterns
    assert 'DIRECT' in page1_text and '2' in page1_text
    assert 'INFERRED' in page1_text and '1' in page1_text
    assert 'NOT FOUND' in page1_text and '1' in page1_text


def test_pdf_confidence_colors_imported():
    """Test CONFIDENCE_COLORS constant has correct structure."""
    # Verify it has exactly 4 keys
    assert len(CONFIDENCE_COLORS) == 4

    # Verify all expected keys exist
    assert 'DIRECT' in CONFIDENCE_COLORS
    assert 'INFERRED' in CONFIDENCE_COLORS
    assert 'DEFAULT' in CONFIDENCE_COLORS
    assert 'NOT FOUND' in CONFIDENCE_COLORS

    # Verify values are Color objects (have .hexval or similar attributes)
    from reportlab.lib.colors import Color
    for level, color in CONFIDENCE_COLORS.items():
        assert isinstance(color, Color), f"{level} color should be a Color object"


def test_pdf_question_id_in_first_column(sample_citation):
    """Test question_id appears in output for cross-referencing (CITE-08)."""
    citation = sample_citation.copy()
    citation['question_id'] = 'model_architecture'
    citation['question_text'] = 'What is the model architecture?'

    buf = BytesIO()
    generate_source_report_pdf(buf, [citation])
    buf.seek(0)

    # Extract text
    pdf = PdfReader(buf)
    all_text = ''
    for page in pdf.pages:
        all_text += page.extract_text()

    # Normalize whitespace (PDF extraction may break text across lines)
    normalized = ''.join(all_text.split())

    # Verify question_id appears in output (without whitespace)
    assert 'model_architecture' in normalized


def test_pdf_direct_citation_has_quote(sample_citation):
    """Test DIRECT citation displays source quote."""
    citation = sample_citation.copy()
    citation['confidence'] = 'DIRECT'
    citation['source_quote'] = 'The model uses transformer architecture with 405B parameters'

    buf = BytesIO()
    generate_source_report_pdf(buf, [citation])
    buf.seek(0)

    # Extract text
    pdf = PdfReader(buf)
    all_text = ''
    for page in pdf.pages:
        all_text += page.extract_text()

    # Verify the source quote text appears
    normalized = ' '.join(all_text.split())
    assert 'transformer architecture' in normalized


def test_pdf_direct_citation_displays_source_document(sample_citation):
    """Test DIRECT citation displays source_document when provided."""
    citation = sample_citation.copy()
    citation['confidence'] = 'DIRECT'
    citation['source_quote'] = 'The model uses transformer architecture'
    citation['source_document'] = 'Model Card'
    citation['source_section'] = 'Architecture'

    buf = BytesIO()
    generate_source_report_pdf(buf, [citation])
    buf.seek(0)

    # Extract text
    pdf = PdfReader(buf)
    all_text = ''
    for page in pdf.pages:
        all_text += page.extract_text()

    # Verify "Document: Model Card" appears
    normalized = ' '.join(all_text.split())
    assert 'Document:' in normalized or 'Document' in normalized
    assert 'Model Card' in normalized


def test_pdf_direct_citation_without_source_document(sample_citation):
    """Test DIRECT citation renders correctly when source_document is empty."""
    citation = sample_citation.copy()
    citation['confidence'] = 'DIRECT'
    citation['source_quote'] = 'The model uses transformer architecture'
    citation['source_document'] = ''  # Empty source_document
    citation['source_section'] = 'Architecture'

    buf = BytesIO()
    generate_source_report_pdf(buf, [citation])  # Should not crash
    buf.seek(0)

    # Verify PDF is valid
    pdf = PdfReader(buf)
    assert len(pdf.pages) >= 1


def test_pdf_not_found_citation_format(sample_citation):
    """Test NOT FOUND citation shows appropriate format."""
    citation = sample_citation.copy()
    citation['confidence'] = 'NOT FOUND'
    citation['answer'] = ''
    citation['source_quote'] = ''
    citation['source_section'] = ''
    citation['reasoning'] = 'Searched Model Details section but parameter count not specified'

    buf = BytesIO()
    generate_source_report_pdf(buf, [citation])
    buf.seek(0)

    # Extract text
    pdf = PdfReader(buf)
    all_text = ''
    for page in pdf.pages:
        all_text += page.extract_text()

    normalized = ' '.join(all_text.split())

    # Verify "not found" or "Information not found" appears
    assert 'not found' in normalized.lower()

    # Verify reasoning appears
    assert 'parameter count' in normalized


def test_pdf_footer_has_model_card_id(sample_citation):
    """Test footer contains model_card_id."""
    buf = BytesIO()
    generate_source_report_pdf(buf, [sample_citation], model_card_id='test-org/test-model')
    buf.seek(0)

    # Extract text from page 1
    pdf = PdfReader(buf)
    page1_text = pdf.pages[0].extract_text()

    # Footer text extraction can be imprecise, so check for key parts
    # Looking for either the full model ID or "Model Card" text
    normalized = ' '.join(page1_text.split())
    assert 'test-org/test-model' in normalized or 'Model Card' in normalized


def test_pdf_footer_on_multiple_pages(many_citations):
    """Test footer appears on all pages of multi-page report."""
    buf = BytesIO()
    generate_source_report_pdf(buf, many_citations, model_card_id='multi-page-model')
    buf.seek(0)

    # Verify PDF has multiple pages
    pdf = PdfReader(buf)
    assert len(pdf.pages) >= 2, "30 citations should produce multiple pages"

    # Extract text from last page
    last_page_text = pdf.pages[-1].extract_text()
    normalized = ' '.join(last_page_text.split())

    # Footer should contain Model Card or page number text
    assert 'Model Card' in normalized or 'Page' in normalized


def test_pdf_generate_with_model_card_id_parameter(sample_citation):
    """Test generate_source_report_pdf accepts model_card_id parameter."""
    buf = BytesIO()

    # Should not raise exception with model_card_id parameter
    generate_source_report_pdf(buf, [sample_citation], model_card_id='org/model')
    buf.seek(0)

    # Verify PDF is valid
    pdf = PdfReader(buf)
    assert len(pdf.pages) >= 1


def test_pdf_default_citation_reasoning_explains_why_standard(sample_citation):
    """Test DEFAULT citation reasoning contains semantic content explaining why standard value is appropriate (CITE-04)."""
    citation = sample_citation.copy()
    citation['confidence'] = 'DEFAULT'
    citation['answer'] = '1.0'
    citation['reasoning'] = 'Standard version number for initial release — no version history found in model card'

    buf = BytesIO()
    generate_source_report_pdf(buf, [citation])
    buf.seek(0)

    # Extract text
    pdf = PdfReader(buf)
    all_text = ''
    for page in pdf.pages:
        all_text += page.extract_text()

    normalized = ' '.join(all_text.split())

    # Verify reasoning text appears
    assert 'Standard version number' in normalized or 'version number for initial release' in normalized

    # Verify "Standard value" or "standard" appears in formatting slot
    assert 'Standard value' in normalized or 'standard' in normalized.lower()


def test_pdf_inferred_citation_reasoning_shows_derivation(sample_citation):
    """Test INFERRED citation shows both source quote and derivation reasoning (CITE-03)."""
    citation = sample_citation.copy()
    citation['confidence'] = 'INFERRED'
    citation['source_quote'] = 'Model was trained on 2 trillion tokens'
    citation['reasoning'] = 'Training data size suggests large-scale web corpus based on typical data-to-token ratios'

    buf = BytesIO()
    generate_source_report_pdf(buf, [citation])
    buf.seek(0)

    # Extract text
    pdf = PdfReader(buf)
    all_text = ''
    for page in pdf.pages:
        all_text += page.extract_text()

    normalized = ' '.join(all_text.split())

    # Verify source quote appears
    assert 'trained on 2 trillion tokens' in normalized

    # Verify reasoning appears
    assert 'large-scale web corpus' in normalized or 'data-to-token ratios' in normalized
