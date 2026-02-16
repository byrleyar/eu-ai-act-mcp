"""Unit tests for citation schema validation."""

import json
import pytest
from pydantic import ValidationError

from citation_schema import (
    ConfidenceLevel,
    Citation,
    CitationReport,
    validate_citation_json,
)


# Happy path tests

def test_valid_citation_all_fields():
    """Valid citation with all fields populated."""
    citation = Citation(
        question_id="Q1",
        question_text="What is the purpose of the AI Act?",
        answer="To regulate AI systems",
        source_quote="This regulation aims to regulate AI systems",
        source_section="Article 1",
        confidence=ConfidenceLevel.DIRECT,
        reasoning="Found exact match in Article 1",
    )

    assert citation.question_id == "Q1"
    assert citation.question_text == "What is the purpose of the AI Act?"
    assert citation.answer == "To regulate AI systems"
    assert citation.source_quote == "This regulation aims to regulate AI systems"
    assert citation.source_section == "Article 1"
    assert citation.confidence == ConfidenceLevel.DIRECT
    assert citation.reasoning == "Found exact match in Article 1"


def test_valid_citation_all_confidence_levels():
    """All 5 ConfidenceLevel values are accepted."""
    for level in ConfidenceLevel:
        citation = Citation(
            question_id="Q1",
            question_text="Test question?",
            confidence=level,
            reasoning="Test reasoning",
        )
        assert citation.confidence == level


def test_valid_citation_empty_optional_strings():
    """Citation with empty answer, source_quote, and source_section is allowed."""
    citation = Citation(
        question_id="Q1",
        question_text="Test question?",
        answer="",
        source_quote="",
        source_section="",
        confidence=ConfidenceLevel.NOT_FOUND,
        reasoning="Information not found in source document",
    )

    assert citation.answer == ""
    assert citation.source_quote == ""
    assert citation.source_section == ""


def test_citation_with_source_document():
    """Citation with source_document field accepts strings and defaults to empty."""
    # Test with source_document provided
    citation_with_doc = Citation(
        question_id="Q1",
        question_text="What is the model architecture?",
        answer="Transformer",
        source_quote="Uses transformer architecture",
        source_section="Architecture",
        source_document="Model Card",
        confidence=ConfidenceLevel.DIRECT,
        reasoning="Found in model card"
    )
    assert citation_with_doc.source_document == "Model Card"

    # Test default empty string
    citation_without_doc = Citation(
        question_id="Q2",
        question_text="Test question?",
        confidence=ConfidenceLevel.DEFAULT,
        reasoning="Standard value"
    )
    assert citation_without_doc.source_document == ""


def test_valid_citation_hallucinated_confidence():
    """Citation with HALLUCINATED confidence is accepted."""
    citation = Citation(
        question_id="Q1",
        question_text="Test?",
        confidence=ConfidenceLevel.HALLUCINATED,
        reasoning="No supporting source found in model card"
    )
    assert citation.confidence == ConfidenceLevel.HALLUCINATED
    assert citation.confidence.value == "HALLUCINATED"


def test_validate_json_hallucinated_confidence():
    """Valid JSON with HALLUCINATED confidence returns CitationReport."""
    valid_json = json.dumps({
        'citations': [
            {
                'question_id': 'Q1',
                'question_text': 'Test question?',
                'confidence': 'HALLUCINATED',
                'reasoning': 'No supporting evidence found',
            }
        ]
    })

    result = validate_citation_json(valid_json)
    assert isinstance(result, CitationReport)
    assert len(result.citations) == 1
    assert result.citations[0].confidence == ConfidenceLevel.HALLUCINATED


def test_valid_report_multiple_citations():
    """CitationReport with multiple citations."""
    citations = [
        Citation(
            question_id=f"Q{i}",
            question_text=f"Question {i}?",
            confidence=ConfidenceLevel.DIRECT,
            reasoning=f"Reasoning {i}",
        )
        for i in range(1, 4)
    ]

    report = CitationReport(citations=citations)
    assert len(report.citations) == 3


# Rejection tests

def test_reject_missing_required_field():
    """Citation missing required field raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        Citation(
            question_text="Test?",
            confidence=ConfidenceLevel.DIRECT,
            reasoning="Test reasoning",
            # missing question_id
        )

    errors = exc_info.value.errors()
    assert any(error['loc'] == ('question_id',) for error in errors)


def test_reject_empty_question_id():
    """Empty question_id violates min_length=1."""
    with pytest.raises(ValidationError) as exc_info:
        Citation(
            question_id="",
            question_text="Test?",
            confidence=ConfidenceLevel.DIRECT,
            reasoning="Test reasoning",
        )

    errors = exc_info.value.errors()
    assert any(
        error['loc'] == ('question_id',) and error['type'] == 'string_too_short'
        for error in errors
    )


def test_reject_whitespace_question_text():
    """Whitespace-only question_text is rejected by field validator."""
    with pytest.raises(ValidationError) as exc_info:
        Citation(
            question_id="Q1",
            question_text="   ",
            confidence=ConfidenceLevel.DIRECT,
            reasoning="Test reasoning",
        )

    errors = exc_info.value.errors()
    assert any(
        error['loc'] == ('question_text',) and 'whitespace' in str(error['msg']).lower()
        for error in errors
    )


def test_reject_whitespace_reasoning():
    """Whitespace-only reasoning is rejected by field validator."""
    with pytest.raises(ValidationError) as exc_info:
        Citation(
            question_id="Q1",
            question_text="Test?",
            confidence=ConfidenceLevel.DIRECT,
            reasoning="  \n  ",
        )

    errors = exc_info.value.errors()
    assert any(
        error['loc'] == ('reasoning',) and 'whitespace' in str(error['msg']).lower()
        for error in errors
    )


def test_reject_invalid_confidence():
    """Invalid confidence level raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        Citation(
            question_id="Q1",
            question_text="Test?",
            confidence="MAYBE",  # type: ignore
            reasoning="Test reasoning",
        )

    errors = exc_info.value.errors()
    assert any(
        error['loc'] == ('confidence',) and error['type'] == 'enum'
        for error in errors
    )


def test_reject_null_confidence():
    """None confidence raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        Citation(
            question_id="Q1",
            question_text="Test?",
            confidence=None,  # type: ignore
            reasoning="Test reasoning",
        )

    errors = exc_info.value.errors()
    assert any(error['loc'] == ('confidence',) for error in errors)


def test_reject_empty_citations_list():
    """CitationReport with empty citations list violates min_length=1."""
    with pytest.raises(ValidationError) as exc_info:
        CitationReport(citations=[])

    errors = exc_info.value.errors()
    assert any(
        error['loc'] == ('citations',) and 'at least 1' in str(error['msg']).lower()
        for error in errors
    )


# validate_citation_json function tests

def test_validate_json_valid():
    """Valid JSON string returns CitationReport."""
    valid_json = json.dumps({
        'citations': [
            {
                'question_id': 'Q1',
                'question_text': 'Test question?',
                'answer': 'Test answer',
                'source_quote': 'Test quote',
                'source_section': 'Section 1',
                'source_document': 'Model Card',
                'confidence': 'DIRECT',
                'reasoning': 'Test reasoning',
            }
        ]
    })

    result = validate_citation_json(valid_json)
    assert isinstance(result, CitationReport)
    assert len(result.citations) == 1
    assert result.citations[0].question_id == 'Q1'
    assert result.citations[0].source_document == 'Model Card'


def test_validate_json_invalid_raises_valueerror():
    """Invalid JSON string raises ValueError with descriptive message."""
    invalid_json = json.dumps({
        'citations': [
            {
                'question_id': '',  # violates min_length=1
                'confidence': 'INVALID',  # invalid enum value
            }
        ]
    })

    with pytest.raises(ValueError) as exc_info:
        validate_citation_json(invalid_json)

    error_message = str(exc_info.value)
    assert len(error_message) > 0


def test_validate_json_malformed_json():
    """Non-JSON string raises ValueError."""
    with pytest.raises(ValueError):
        validate_citation_json("not valid json")


def test_validate_json_error_message_contains_field_path():
    """Error message includes field path like 'citations -> 0 -> confidence'."""
    invalid_json = json.dumps({
        'citations': [
            {
                'question_id': 'Q1',
                'question_text': 'Test?',
                'confidence': 'INVALID_VALUE',
                'reasoning': 'Test',
            }
        ]
    })

    with pytest.raises(ValueError) as exc_info:
        validate_citation_json(invalid_json)

    error_message = str(exc_info.value)
    assert 'citations' in error_message
    assert '0' in error_message
    assert 'confidence' in error_message
