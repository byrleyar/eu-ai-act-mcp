import pytest
from citation_schema import Citation, CitationReport, ConfidenceLevel, validate_report_coverage

def test_validate_report_coverage_success():
    """Test that validation passes when all required IDs are present."""
    required_ids = ["Q1", "Q2"]
    citations = [
        Citation(
            question_id="Q1",
            question_text="Q1 text",
            answer="A1",
            confidence=ConfidenceLevel.DIRECT,
            reasoning="R1"
        ),
        Citation(
            question_id="Q2",
            question_text="Q2 text",
            answer="A2",
            confidence=ConfidenceLevel.DIRECT,
            reasoning="R2"
        )
    ]
    report = CitationReport(citations=citations)
    
    # Should not raise
    validate_report_coverage(report, required_ids)

def test_validate_report_coverage_missing_ids():
    """Test that validation fails when some required IDs are missing."""
    required_ids = ["Q1", "Q2", "Q3"]
    citations = [
        Citation(
            question_id="Q1",
            question_text="Q1 text",
            answer="A1",
            confidence=ConfidenceLevel.DIRECT,
            reasoning="R1"
        )
    ]
    report = CitationReport(citations=citations)
    
    with pytest.raises(ValueError) as excinfo:
        validate_report_coverage(report, required_ids)
    
    assert "Missing citations for 2 questions: [Q2, Q3]" in str(excinfo.value)

def test_validate_report_coverage_empty_required():
    """Test that validation passes when no IDs are required."""
    required_ids = []
    citations = [
        Citation(
            question_id="Q1",
            question_text="Q1 text",
            answer="A1",
            confidence=ConfidenceLevel.DIRECT,
            reasoning="R1"
        )
    ]
    report = CitationReport(citations=citations)
    
    # Should not raise
    validate_report_coverage(report, required_ids)

def test_validate_report_coverage_extra_ids():
    """Test that validation passes when extra IDs are present."""
    required_ids = ["Q1"]
    citations = [
        Citation(
            question_id="Q1",
            question_text="Q1 text",
            answer="A1",
            confidence=ConfidenceLevel.DIRECT,
            reasoning="R1"
        ),
        Citation(
            question_id="Q2",
            question_text="Q2 text",
            answer="A2",
            confidence=ConfidenceLevel.DIRECT,
            reasoning="R2"
        )
    ]
    report = CitationReport(citations=citations)
    
    # Should not raise
    validate_report_coverage(report, required_ids)
