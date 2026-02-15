"""PDF generation for citation reports using ReportLab.

This module provides pure functions for generating PDF reports from citation data.
All text rendering uses Unicode-compatible DejaVu Sans font to handle smart quotes,
accented characters, and other special characters. Tables auto-wrap long text and
repeat headers on multi-page reports.

Exports:
    generate_source_report_pdf: Function to generate a PDF citation report
"""

import os
import html
from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# Register DejaVu Sans font at module load
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts')
pdfmetrics.registerFont(TTFont('DejaVuSans', os.path.join(FONT_DIR, 'DejaVuSans.ttf')))


def _escape_xml(text: str) -> str:
    """Escape XML special characters in text before embedding in Paragraph markup.

    Args:
        text: Raw text string that may contain &, <, >, or " characters

    Returns:
        XML-safe string with special characters escaped
    """
    return html.escape(text)


def generate_source_report_pdf(output_stream: BytesIO, citations: list[dict]) -> None:
    """Generate a PDF citation report from validated citation data.

    This function creates a multi-page PDF with a title, timestamp, and table of
    citations. The table auto-wraps long text and repeats headers on each page.
    All text is rendered using DejaVu Sans font to support Unicode characters.

    Args:
        output_stream: BytesIO stream to write the PDF to
        citations: List of citation dictionaries (pre-validated by citation_schema)
                   Each citation should have: question_id, question_text, answer,
                   source_quote, source_section, confidence, reasoning

    Returns:
        None. The PDF is written to output_stream. Caller is responsible for
        seeking to position 0 if they need to read from the stream.

    Example:
        >>> from io import BytesIO
        >>> from citation_schema import validate_citation_json
        >>> import json
        >>> data = json.dumps({'citations': [{'question_id': 'Q1', ...}]})
        >>> report = validate_citation_json(data)
        >>> buf = BytesIO()
        >>> generate_source_report_pdf(buf, [c.model_dump() for c in report.citations])
        >>> buf.seek(0)
        >>> pdf_bytes = buf.read()
    """
    # Create document with margins
    doc = SimpleDocTemplate(
        output_stream,
        pagesize=letter,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch
    )

    # Define paragraph styles using DejaVu Sans font
    title_style = ParagraphStyle(
        'TitleStyle',
        fontName='DejaVuSans',
        fontSize=16,
        spaceAfter=12
    )

    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        fontName='DejaVuSans',
        fontSize=10,
        spaceAfter=6,
        textColor=colors.grey
    )

    cell_text_style = ParagraphStyle(
        'CellText',
        fontName='DejaVuSans',
        fontSize=8,
        leading=10
    )

    header_text_style = ParagraphStyle(
        'HeaderText',
        fontName='DejaVuSans',
        fontSize=9,
        textColor=colors.white
    )

    # Build story (list of flowables)
    story = []

    # Add title
    story.append(Paragraph("AI Act Compliance - Source Citation Report", title_style))

    # Add subtitle with timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    story.append(Paragraph(f"Generated: {timestamp}", subtitle_style))

    # Add spacer
    story.append(Spacer(1, 0.3 * inch))

    # Build table data
    # Header row
    headers = ['#', 'Question', 'Answer', 'Source Quote', 'Section', 'Confidence', 'Reasoning']
    header_row = [Paragraph(_escape_xml(h), header_text_style) for h in headers]

    # Data rows
    table_data = [header_row]
    for idx, citation in enumerate(citations, start=1):
        row = [
            Paragraph(_escape_xml(str(idx)), cell_text_style),
            Paragraph(_escape_xml(citation.get('question_text', '')), cell_text_style),
            Paragraph(_escape_xml(citation.get('answer', '')), cell_text_style),
            Paragraph(_escape_xml(citation.get('source_quote', '')), cell_text_style),
            Paragraph(_escape_xml(citation.get('source_section', '')), cell_text_style),
            Paragraph(_escape_xml(citation.get('confidence', '')), cell_text_style),
            Paragraph(_escape_xml(citation.get('reasoning', '')), cell_text_style),
        ]
        table_data.append(row)

    # Create table with column widths
    col_widths = [
        0.3 * inch,  # #
        1.3 * inch,  # Question
        1.5 * inch,  # Answer
        2.0 * inch,  # Source Quote
        0.6 * inch,  # Section
        0.7 * inch,  # Confidence
        1.1 * inch,  # Reasoning
    ]

    table = Table(table_data, colWidths=col_widths, repeatRows=1)

    # Apply table style
    table.setStyle(TableStyle([
        # Header row styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A5568')),  # Dark grey
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),

        # Data rows styling
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F7FAFC')]),  # Alternating
        ('VALIGN', (0, 1), (-1, -1), 'TOP'),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),

        # Grid lines
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),

        # Padding
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))

    story.append(table)

    # Build PDF
    doc.build(story)
