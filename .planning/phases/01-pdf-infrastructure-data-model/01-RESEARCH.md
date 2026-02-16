# Phase 1: PDF Infrastructure & Data Model - Research

**Researched:** 2026-02-15
**Domain:** PDF generation with ReportLab and data validation with Pydantic
**Confidence:** HIGH

## Summary

Phase 1 establishes PDF generation infrastructure using ReportLab 4.4.10 (released Feb 12, 2026) for creating structurally sound, Unicode-compatible compliance reports in-memory, paired with Pydantic 2.12.5 for strict citation data schema validation.

ReportLab's Platypus framework (SimpleDocTemplate, Paragraph, Table flowables) provides high-level document composition with BytesIO for in-memory generation. DejaVu Sans font registration prevents Unicode encoding crashes on special characters. Table auto-wrapping is achieved by wrapping cell content in Paragraph flowables with defined column widths. Multi-page header repetition uses the repeatRows parameter on Table instances.

Pydantic v2 BaseModel with Field constraints enforces strict schema validation, rejecting malformed citation JSON with detailed error messages specifying field location, error type, and input value. The model_validate_json classmethod handles JSON parsing and validation in a single operation.

**Primary recommendation:** Use SimpleDocTemplate with BytesIO buffer and Paragraph-wrapped table cells for auto-wrapping. Register DejaVu Sans font at module initialization. Define citation schema as Pydantic BaseModel with strict Field validation.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| reportlab | 4.4.10 | PDF generation | Industry-standard Python PDF library since 2000, actively maintained, supports Python 3.9-3.14 |
| pydantic | 2.12.5 | Data validation and schema definition | De facto standard for Python data validation, provides automatic JSON schema generation and clear error messages |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-docx | 1.2.0 | Word document generation (existing) | Already in use for DOCX generation, pattern to mirror for consistency |
| pytest | latest | Unit testing PDF generation | Testing PDF output with mock citation data |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| ReportLab | fpdf2 (2.8.5 already installed) | fpdf2 is simpler but lacks Platypus framework's automatic layout management and has weaker Unicode support |
| ReportLab | WeasyPrint | WeasyPrint uses HTML/CSS which adds complexity and dependencies (WebKit rendering engine) |
| Pydantic | dataclasses + manual validation | Loses automatic JSON schema generation, validation error detail, and ecosystem tooling |

**Installation:**
```bash
# Already in requirements.txt:
# reportlab==4.4.10 (implied by ReportLab decision)
# pydantic==2.12.5
# pydantic_core==2.41.5

# Add if needed for DejaVu Sans font (or download manually):
# dejavu-sans-fonts package OR download from https://dejavu-fonts.github.io/
```

## Architecture Patterns

### Recommended Project Structure
```
/
├── pdf_generator.py         # PDF generation pure function (mirrors docx_generator.py)
├── citation_schema.py        # Pydantic citation data models
├── server.py                 # MCP tool registration (existing)
└── tests/
    └── test_pdf_generator.py  # Unit tests with mock citation data
```

### Pattern 1: Pure Function PDF Generation (Mirror Existing DOCX Pattern)
**What:** Generator accepts in-memory streams, returns nothing, has no side effects
**When to use:** All PDF generation operations
**Example:**
```python
# Source: Based on existing docx_generator.py pattern
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, Paragraph, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def generate_pdf_report(output_stream: BytesIO, citation_data: list[dict]) -> None:
    """
    Generate PDF report from citation data.

    Args:
        output_stream: BytesIO buffer to write PDF content
        citation_data: List of citation dictionaries (pre-validated)

    Returns:
        None (modifies output_stream in-place)
    """
    # Build PDF using SimpleDocTemplate + flowables
    doc = SimpleDocTemplate(output_stream, pagesize=letter)

    # Build story (list of flowables)
    story = []
    # ... add content ...

    doc.build(story)
```

### Pattern 2: Font Registration at Module Load
**What:** Register DejaVu Sans once when module is imported
**When to use:** PDF generator module initialization
**Example:**
```python
# Source: ReportLab docs - https://docs.reportlab.com/reportlab/userguide/ch3_fonts/
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register at module load (not inside function)
pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))

# Then use in styles:
from reportlab.lib.styles import ParagraphStyle
style = ParagraphStyle('Normal', fontName='DejaVuSans', fontSize=10)
```

### Pattern 3: Table Cell Auto-Wrapping with Paragraphs
**What:** Wrap table cell strings in Paragraph flowables with defined column widths
**When to use:** Any table with variable-length text content
**Example:**
```python
# Source: ReportLab docs - https://docs.reportlab.com/reportlab/userguide/ch7_tables/
from reportlab.platypus import Table, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

styles = getSampleStyleSheet()

# Data with Paragraph-wrapped cells for auto-wrapping
data = [
    ['Question', 'Answer', 'Confidence'],  # Headers
    [
        Paragraph('What is the system purpose?', styles['Normal']),
        Paragraph('Very long answer that will auto-wrap to multiple lines within the cell width...', styles['Normal']),
        Paragraph('DIRECT', styles['Normal'])
    ]
]

# Define column widths (required for Paragraph wrapping)
t = Table(data, colWidths=[2*inch, 4*inch, 1*inch], repeatRows=1)
```

### Pattern 4: Pydantic Schema with Clear Validation
**What:** Define citation schema as BaseModel with Field constraints
**When to use:** Before any PDF generation, at MCP tool entry point
**Example:**
```python
# Source: Pydantic docs - https://docs.pydantic.dev/latest/api/base_model/
from pydantic import BaseModel, Field, ValidationError
from enum import Enum

class ConfidenceLevel(str, Enum):
    DIRECT = "DIRECT"
    INFERRED = "INFERRED"
    DEFAULT = "DEFAULT"
    NOT_FOUND = "NOT FOUND"

class Citation(BaseModel):
    question_id: str = Field(min_length=1)
    question_text: str = Field(min_length=1)
    answer: str  # Can be empty string
    source_quote: str
    source_section: str
    confidence: ConfidenceLevel
    reasoning: str = Field(min_length=1)

# Validate JSON input
def validate_citations(json_data: str) -> list[Citation]:
    try:
        citations = [Citation.model_validate(item) for item in json.loads(json_data)]
        return citations
    except ValidationError as e:
        # e.errors() returns detailed error list
        raise ValueError(f"Citation validation failed: {e.errors()}")
```

### Pattern 5: MCP Tool Integration (Follow Existing Pattern)
**What:** MCP tool receives JSON, validates, generates PDF, returns BytesIO buffer
**When to use:** @mcp.tool() decorator in server.py
**Example:**
```python
# Source: Based on existing server.py pattern with docx_generator
from mcp.server.fastmcp import FastMCP
import io
import base64
from citation_schema import validate_citations
from pdf_generator import generate_pdf_report

@mcp.tool()
def generate_source_report(citation_json: str) -> dict:
    """Generate PDF report from citation data."""

    # 1. Validate input
    try:
        citations = validate_citations(citation_json)
    except ValueError as e:
        return {"error": str(e)}

    # 2. Generate PDF in-memory
    buffer = io.BytesIO()
    generate_pdf_report(buffer, [c.model_dump() for c in citations])

    # 3. Return as base64 or save to disk (existing pattern)
    buffer.seek(0)
    return {
        "content": base64.b64encode(buffer.read()).decode('utf-8'),
        "format": "pdf"
    }
```

### Anti-Patterns to Avoid
- **File I/O in generator function:** Keep PDF generation pure - accept BytesIO, don't write to disk (mirrors docx_generator.py pattern)
- **Plain strings in table cells:** Use Paragraph flowables for auto-wrapping, not plain strings which accumulate in messy clumps
- **Hardcoded fonts:** Always register DejaVu Sans or Unicode-compatible font to prevent encoding crashes
- **Validating inside generator:** Validate at MCP tool boundary, pass clean data to generator
- **Manual column width calculation:** Define explicit colWidths for tables with Paragraphs (None causes unpredictable wrapping)

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Text wrapping in table cells | Custom line-breaking logic | ReportLab Paragraph flowables in table cells | Paragraph handles word boundaries, hyphenation, style inheritance, and multi-line calculations automatically |
| Font subsetting/embedding | Manual TTF parsing and subset generation | ReportLab TTFont with pdfmetrics.registerFont | ReportLab performs automatic font subsetting, embedding, and PDF object creation |
| PDF structure generation | Manual PDF byte stream construction | SimpleDocTemplate + Platypus flowables | Platypus handles page breaks, frame overflow, coordinate transformations, and PDF compression automatically |
| JSON schema validation | if/else type checks and manual error messages | Pydantic BaseModel with Field constraints | Pydantic provides automatic type coercion, nested validation, detailed error messages, and JSON schema generation |
| Multi-page table splitting | Manual row height calculation and page break logic | Table with repeatRows parameter + SimpleDocTemplate auto-split | ReportLab automatically calculates available space, splits tables across pages, and repeats headers |

**Key insight:** PDF generation has deceptively complex edge cases (Unicode normalization, font metrics, coordinate systems, page overflow). ReportLab and Pydantic are battle-tested solutions handling thousands of edge cases. Custom solutions will inevitably rediscover these edge cases through production bugs.

## Common Pitfalls

### Pitfall 1: Forgetting to Register Unicode Font
**What goes wrong:** PDF generation crashes with encoding errors when encountering smart quotes, em-dashes, or non-Latin characters
**Why it happens:** ReportLab's default fonts (Helvetica, Times, Courier) only support WinAnsi encoding (subset of Latin-1), not full Unicode
**How to avoid:** Register DejaVu Sans or other Unicode TTF font at module initialization before any PDF generation
**Warning signs:** UnicodeEncodeError or "character not in WinAnsi encoding" errors during PDF generation

### Pitfall 2: Plain Strings in Table Cells Without Column Widths
**What goes wrong:** Long text content accumulates in one messy clump without wrapping
**Why it happens:** ReportLab doesn't auto-wrap plain strings; None column width means auto-calculate based on content, which doesn't wrap text
**How to avoid:** Wrap cell content in Paragraph flowables AND define explicit colWidths
**Warning signs:** Table cells horizontally overflow page margins or text appears truncated

### Pitfall 3: Translation/Scaling Moving Content Off Page
**What goes wrong:** PDF generates successfully but appears blank
**Why it happens:** Coordinate transformations (translate/scale) can move drawing operations outside visible page area
**How to avoid:** Use Platypus framework (SimpleDocTemplate) which manages coordinates automatically; avoid manual canvas transforms unless necessary
**Warning signs:** PDF file size is reasonable but pages render blank or partially blank

### Pitfall 4: Not Calling buffer.seek(0) After PDF Generation
**What goes wrong:** Reading buffer returns empty bytes or partial content
**Why it happens:** After doc.build(), buffer position is at end of stream; reading returns nothing
**How to avoid:** Always call buffer.seek(0) before reading buffer content or passing to response
**Warning signs:** PDF downloads are 0 bytes or corrupt/truncated

### Pitfall 5: Pydantic Validation Errors Lost in Generic Exception Handling
**What goes wrong:** User receives "validation failed" without details about which field or why
**Why it happens:** ValidationError.errors() returns detailed error list but generic str(e) loses structure
**How to avoid:** Access e.errors() to get field-level error details, format into actionable error message
**Warning signs:** Users report "doesn't work" without ability to fix their input data

### Pitfall 6: Forgetting repeatRows for Multi-Page Tables
**What goes wrong:** Second and subsequent pages of table have no headers, making data unreadable
**Why it happens:** Table splits across pages but repeatRows defaults to 0 (no header repetition)
**How to avoid:** Set repeatRows=1 (or number of header rows) when creating Table instance
**Warning signs:** Multi-page PDFs have headers only on first page

### Pitfall 7: Unclosed Tags in Paragraph Markup
**What goes wrong:** PDF compilation fails with cryptic XML parsing errors
**Why it happens:** Paragraph content supports XML markup (<b>, <i>, etc.) but malformed markup breaks parser
**How to avoid:** Escape user-provided text content or use plain text without markup; if using markup, validate tag closure
**Warning signs:** "Error in para markup" or "unmatched tag" errors

## Code Examples

Verified patterns from official sources:

### Complete PDF Generation with Table and Auto-Wrapping
```python
# Source: Combined from ReportLab docs
# - https://docs.reportlab.com/reportlab/userguide/ch5_platypus/
# - https://docs.reportlab.com/reportlab/userguide/ch7_tables/
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, Paragraph, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register Unicode font (do once at module load)
pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))

def generate_citation_pdf(output_stream: BytesIO, citations: list[dict]) -> None:
    """Generate PDF report from citation data."""

    # Create document
    doc = SimpleDocTemplate(output_stream, pagesize=letter,
                           topMargin=0.5*inch, bottomMargin=0.5*inch)

    # Define styles with Unicode font
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CellText', fontName='DejaVuSans', fontSize=9))
    styles.add(ParagraphStyle(name='Header', fontName='DejaVuSans', fontSize=10,
                              textColor=colors.white))

    # Build story
    story = []

    # Title
    title_style = ParagraphStyle('Title', fontName='DejaVuSans', fontSize=16,
                                 spaceAfter=12)
    story.append(Paragraph("AI Act Compliance Source Report", title_style))
    story.append(Spacer(1, 0.2*inch))

    # Build table data with Paragraph-wrapped cells
    table_data = [
        # Header row
        [Paragraph('<b>Question</b>', styles['Header']),
         Paragraph('<b>Answer</b>', styles['Header']),
         Paragraph('<b>Source Quote</b>', styles['Header']),
         Paragraph('<b>Confidence</b>', styles['Header'])]
    ]

    for citation in citations:
        table_data.append([
            Paragraph(citation['question_text'], styles['CellText']),
            Paragraph(citation['answer'], styles['CellText']),
            Paragraph(citation['source_quote'], styles['CellText']),
            Paragraph(citation['confidence'], styles['CellText'])
        ])

    # Create table with explicit column widths and repeating headers
    table = Table(table_data,
                  colWidths=[1.5*inch, 2*inch, 2.5*inch, 1*inch],
                  repeatRows=1)

    # Apply table styling
    table.setStyle(TableStyle([
        # Header row styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'DejaVuSans'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

        # Data rows styling
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 1), (-1, -1), 'DejaVuSans'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))

    story.append(table)

    # Build PDF
    doc.build(story)
```

### Pydantic Citation Schema Validation
```python
# Source: Pydantic docs - https://docs.pydantic.dev/latest/api/base_model/
from pydantic import BaseModel, Field, ValidationError, field_validator
from enum import Enum
from typing import List
import json

class ConfidenceLevel(str, Enum):
    DIRECT = "DIRECT"
    INFERRED = "INFERRED"
    DEFAULT = "DEFAULT"
    NOT_FOUND = "NOT FOUND"

class Citation(BaseModel):
    """Citation data model with strict validation."""

    question_id: str = Field(min_length=1, description="Unique question identifier")
    question_text: str = Field(min_length=1, description="Full question text")
    answer: str = Field(description="Answer text (may be empty)")
    source_quote: str = Field(description="Relevant quote from source document")
    source_section: str = Field(description="Section identifier in source")
    confidence: ConfidenceLevel = Field(description="Confidence level for citation")
    reasoning: str = Field(min_length=1, description="Explanation of confidence level")

    @field_validator('question_text', 'reasoning')
    @classmethod
    def not_empty_string(cls, v: str, info) -> str:
        """Ensure required strings are not just whitespace."""
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} cannot be empty or whitespace")
        return v.strip()

class CitationReport(BaseModel):
    """Container for citation list with metadata."""
    citations: List[Citation] = Field(min_length=1)

# Usage in MCP tool
def validate_citation_json(json_string: str) -> CitationReport:
    """
    Validate citation JSON with detailed error reporting.

    Raises:
        ValueError: With detailed validation errors
    """
    try:
        report = CitationReport.model_validate_json(json_string)
        return report
    except ValidationError as e:
        # Format detailed error messages
        errors = []
        for error in e.errors():
            field_path = ' -> '.join(str(loc) for loc in error['loc'])
            errors.append(f"{field_path}: {error['msg']} (type: {error['type']})")

        raise ValueError(
            f"Citation validation failed:\n" + "\n".join(f"  - {err}" for err in errors)
        )

# Example error message output:
# Citation validation failed:
#   - citations -> 0 -> confidence: Input should be 'DIRECT', 'INFERRED', 'DEFAULT' or 'NOT FOUND' (type: enum)
#   - citations -> 1 -> question_id: Field required (type: missing)
#   - citations -> 2 -> reasoning: reasoning cannot be empty or whitespace (type: value_error)
```

### Unit Test Pattern for PDF Generation
```python
# Source: pytest best practices + ReportLab BytesIO pattern
import pytest
from io import BytesIO
from pypdf import PdfReader

def test_pdf_generation_basic():
    """Test basic PDF generation with valid citation data."""
    # Arrange
    citations = [{
        'question_id': 'Q1',
        'question_text': 'What is the system purpose?',
        'answer': 'Risk assessment for AI systems',
        'source_quote': 'The system performs risk assessment...',
        'source_section': 'Section 3.2',
        'confidence': 'DIRECT',
        'reasoning': 'Explicitly stated in documentation'
    }]
    buffer = BytesIO()

    # Act
    generate_citation_pdf(buffer, citations)

    # Assert
    buffer.seek(0)
    pdf = PdfReader(buffer)
    assert len(pdf.pages) >= 1
    assert 'What is the system purpose?' in pdf.pages[0].extract_text()

def test_pdf_handles_unicode():
    """Test PDF generation with Unicode special characters."""
    citations = [{
        'question_id': 'Q1',
        'question_text': 'Testing "smart quotes" and em-dash—here',
        'answer': 'Réponse avec accénts: café, naïve, résumé',
        'source_quote': '日本語 characters: こんにちは',
        'source_section': 'Section 1',
        'confidence': 'INFERRED',
        'reasoning': 'Unicode test'
    }]
    buffer = BytesIO()

    # Should not raise encoding errors
    generate_citation_pdf(buffer, citations)

    buffer.seek(0)
    pdf = PdfReader(buffer)
    text = pdf.pages[0].extract_text()
    assert 'smart quotes' in text or '"' in text  # pypdf may normalize quotes

def test_pdf_long_text_wrapping():
    """Test table auto-wrapping with very long quote (1000+ chars)."""
    long_quote = "Lorem ipsum " * 100  # ~1200 characters
    citations = [{
        'question_id': 'Q1',
        'question_text': 'Long content test',
        'answer': 'Short answer',
        'source_quote': long_quote,
        'source_section': 'Section 1',
        'confidence': 'DEFAULT',
        'reasoning': 'Long text wrapping test'
    }]
    buffer = BytesIO()

    # Should not raise overflow or data loss errors
    generate_citation_pdf(buffer, citations)

    buffer.seek(0)
    pdf = PdfReader(buffer)
    assert len(pdf.pages) >= 1  # Content should fit, possibly multi-page

def test_pdf_multipage_header_repetition():
    """Test that headers repeat on multi-page tables."""
    # Create enough citations to force multi-page table
    citations = [
        {
            'question_id': f'Q{i}',
            'question_text': f'Question {i} with moderate length text',
            'answer': f'Answer {i} ' * 10,
            'source_quote': f'Source quote {i} ' * 15,
            'source_section': f'Section {i}',
            'confidence': 'DIRECT',
            'reasoning': f'Reasoning {i}'
        }
        for i in range(30)  # Likely to create 2+ pages
    ]
    buffer = BytesIO()

    generate_citation_pdf(buffer, citations)

    buffer.seek(0)
    pdf = PdfReader(buffer)

    if len(pdf.pages) > 1:
        # Check that header text appears on multiple pages
        page1_text = pdf.pages[0].extract_text()
        page2_text = pdf.pages[1].extract_text()
        assert 'Question' in page1_text
        assert 'Question' in page2_text  # Header should repeat
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| ReportLab v3.x pagesizes import from reportlab.lib.pagesizes | Same (stable API) | N/A | No change needed, API stable since v3 |
| Pydantic v1 validator decorator | Pydantic v2 @field_validator with classmethod | Pydantic v2 (2023) | Must use @field_validator(mode='before'/'after') and @classmethod |
| Pydantic v1 .dict() and .json() | Pydantic v2 .model_dump() and .model_dump_json() | Pydantic v2 (2023) | Old methods deprecated, use model_* equivalents |
| Manual Type 1 font registration | TTFont for TrueType fonts | Long established | TTFont is standard for Unicode fonts like DejaVu Sans |

**Deprecated/outdated:**
- **Pydantic v1 API:** .dict(), .json(), .schema(), validator decorator without @classmethod
- **fpdf (original):** Superseded by fpdf2, but ReportLab is more mature for complex layouts

## Open Questions

1. **DejaVu Sans font file location**
   - What we know: Can register with pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
   - What's unclear: Best practice for font file distribution - package with code, expect system installation, or download at runtime?
   - Recommendation: Include DejaVuSans.ttf in repository /fonts directory, use relative path from pdf_generator.py. Fallback to system font directories if not found.

2. **PDF file size with large citation datasets**
   - What we know: ReportLab performs automatic font subsetting and compression
   - What's unclear: At what citation count does PDF size become problematic for MCP transport (base64 encoded)?
   - Recommendation: Test with 100+ citation dataset. If size is issue, implement pagination or multi-file generation.

3. **Confidence level color coding**
   - What we know: TableStyle supports per-cell background colors
   - What's unclear: User requirement doesn't specify color coding, but would enhance readability
   - Recommendation: Implement basic styling in Phase 1 (header row background), defer color-by-confidence to future enhancement unless specified in testing feedback.

## Sources

### Primary (HIGH confidence)
- [ReportLab Official Documentation - Tables](https://docs.reportlab.com/reportlab/userguide/ch7_tables/) - Table creation, cell wrapping, column widths, repeatRows
- [ReportLab Official Documentation - Fonts](https://docs.reportlab.com/reportlab/userguide/ch3_fonts/) - TTFont registration, Unicode support
- [ReportLab Official Documentation - Platypus](https://docs.reportlab.com/reportlab/userguide/ch5_platypus/) - SimpleDocTemplate, flowables, document building
- [Pydantic Validation Errors Documentation](https://docs.pydantic.dev/latest/errors/validation_errors/) - Error structure, types, handling
- [Pydantic BaseModel API Documentation](https://docs.pydantic.dev/latest/api/base_model/) - model_validate_json, ValidationError, Field usage
- [ReportLab PyPI](https://pypi.org/project/reportlab/) - Version 4.4.10 release info (Feb 12, 2026)

### Secondary (MEDIUM confidence)
- [Django Documentation - PDF Creation](https://django.readthedocs.io/en/stable/howto/outputting-pdf.html) - BytesIO pattern with ReportLab
- [ReportLab Quick Start Guide](https://docs.reportlab.com/rmlfornewbies/) - Common pitfalls, best practices
- [Pydantic Strict Mode Documentation](https://docs.pydantic.dev/latest/concepts/strict_mode/) - Strict validation configuration
- [DejaVu Fonts Official Site](https://dejavu-fonts.github.io/) - Font download and information

### Tertiary (LOW confidence - WebSearch only)
- Various blog posts and tutorials on ReportLab table wrapping - consistent patterns observed across sources but not verified with official docs

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - ReportLab and Pydantic are verified as current standard solutions with official documentation
- Architecture: HIGH - Patterns verified from official ReportLab docs and existing project code (docx_generator.py)
- Pitfalls: MEDIUM-HIGH - Pitfalls sourced from official ReportLab FAQ and verified through multiple community sources
- Code examples: HIGH - All examples derived from official documentation with adaptations for project requirements

**Research date:** 2026-02-15
**Valid until:** 2026-03-15 (30 days - both libraries are stable with infrequent breaking changes)
