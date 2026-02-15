"""Citation data models with Pydantic validation.

This module defines the data contract between MCP tool input and PDF generation.
Strict validation at the boundary prevents malformed data from reaching the PDF
generator, producing clear error messages that help users fix their input.

Exports:
    ConfidenceLevel: Enum for citation confidence levels
    Citation: Model for a single question-answer citation
    CitationReport: Container for a list of citations
    validate_citation_json: Function to validate JSON string and return CitationReport
"""

from enum import Enum
from pydantic import BaseModel, Field, ValidationError, field_validator


class ConfidenceLevel(str, Enum):
    """Confidence level for a citation."""
    DIRECT = "DIRECT"
    INFERRED = "INFERRED"
    DEFAULT = "DEFAULT"
    NOT_FOUND = "NOT FOUND"


class Citation(BaseModel):
    """A single question-answer citation with source information."""

    question_id: str = Field(min_length=1)
    question_text: str = Field(min_length=1)
    answer: str = Field(default="")
    source_quote: str = Field(default="")
    source_section: str = Field(default="")
    confidence: ConfidenceLevel
    reasoning: str = Field(min_length=1)

    @field_validator('question_text', mode='after')
    @classmethod
    def validate_question_text_not_whitespace(cls, v: str) -> str:
        """Reject whitespace-only question text."""
        if not v.strip():
            raise ValueError("question_text cannot be whitespace-only")
        return v

    @field_validator('reasoning', mode='after')
    @classmethod
    def validate_reasoning_not_whitespace(cls, v: str) -> str:
        """Reject whitespace-only reasoning."""
        if not v.strip():
            raise ValueError("reasoning cannot be whitespace-only")
        return v


class CitationReport(BaseModel):
    """Container for a list of citations."""

    citations: list[Citation] = Field(min_length=1)


def validate_citation_json(json_string: str) -> CitationReport:
    """Validate a JSON string and return a CitationReport instance.

    Args:
        json_string: JSON string to validate

    Returns:
        CitationReport instance if validation succeeds

    Raises:
        ValueError: If validation fails, with formatted field-level error messages
    """
    try:
        return CitationReport.model_validate_json(json_string)
    except ValidationError as e:
        # Format errors to show field paths
        error_messages = []
        for error in e.errors():
            # Build field path (e.g., "citations -> 0 -> confidence")
            field_path = " -> ".join(str(loc) for loc in error['loc'])
            error_type = error['type']
            msg = error['msg']
            error_messages.append(f"{field_path}: {msg} (type: {error_type})")

        error_string = "; ".join(error_messages)
        raise ValueError(error_string)
