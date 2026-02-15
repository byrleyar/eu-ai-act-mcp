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

# WCAG AA compliant confidence level colors (4.5:1+ contrast with black text)
CONFIDENCE_COLORS = {
    'DIRECT': colors.HexColor('#D4EDDA'),      # Light green
    'INFERRED': colors.HexColor('#FFF3CD'),    # Light yellow
    'DEFAULT': colors.HexColor('#E7E8EA'),     # Light gray
    'NOT FOUND': colors.HexColor('#F8D7DA')    # Light red
}


def _escape_xml(text: str) -> str:
    """Escape XML special characters in text before embedding in Paragraph markup.

    Args:
        text: Raw text string that may contain &, <, >, or " characters

    Returns:
        XML-safe string with special characters escaped
    """
    return html.escape(text)


def _create_footer_callback(model_card_id: str):
    """Create a footer callback function for PDF pages.

    Args:
        model_card_id: Model card identifier to display in footer

    Returns:
        Callback function with signature (canvas, doc) for use with doc.build()
    """
    def footer_callback(canvas, doc):
        """Draw footer on each page with model card ID and timestamp."""
        canvas.saveState()

        # Set footer text properties
        canvas.setFont('DejaVuSans', 8)
        canvas.setFillGray(0.4)

        # Left side: Model Card ID
        canvas.drawString(0.5 * inch, 0.3 * inch, f"Model Card: {model_card_id}")

        # Right side: Timestamp and page number
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        right_text = f"Generated: {timestamp} | Page {doc.page}"
        canvas.drawRightString(doc.pagesize[0] - 0.5 * inch, 0.3 * inch, right_text)

        canvas.restoreState()

    return footer_callback


def _build_executive_summary(citations: list[dict], model_card_id: str):
    """Build executive summary flowables showing confidence breakdown.

    Args:
        citations: List of citation dictionaries
        model_card_id: Model card identifier string

    Returns:
        List of flowables (Paragraphs and Spacers) for executive summary section
    """
    from collections import Counter

    # Define styles for summary
    summary_header_style = ParagraphStyle(
        'SummaryHeader',
        fontName='DejaVuSans',
        fontSize=14,
        spaceAfter=8
    )

    summary_body_style = ParagraphStyle(
        'SummaryBody',
        fontName='DejaVuSans',
        fontSize=10,
        leading=14
    )

    flowables = []

    # Add header
    flowables.append(Paragraph("Executive Summary", summary_header_style))
    flowables.append(Spacer(1, 0.1 * inch))

    # Handle zero citations
    if not citations:
        flowables.append(Paragraph("No citations provided.", summary_body_style))
        return flowables

    # Count confidence levels
    confidence_counts = Counter(c.get('confidence', 'UNKNOWN') for c in citations)
    total = len(citations)

    # Build summary text
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')

    summary_lines = [
        f"<b>Model Card:</b> {_escape_xml(model_card_id)}",
        f"<b>Generated:</b> {timestamp}",
        f"<b>Total Questions:</b> {total}",
        "",
        "<b>Confidence Breakdown:</b>"
    ]

    # Add breakdown for each level
    for level in ['DIRECT', 'INFERRED', 'DEFAULT', 'NOT FOUND']:
        count = confidence_counts.get(level, 0)
        percentage = (count / total * 100) if total > 0 else 0
        summary_lines.append(f"  • {level}: {count} ({percentage:.1f}%)")

    summary_text = "<br/>".join(summary_lines)
    flowables.append(Paragraph(summary_text, summary_body_style))

    return flowables


def generate_source_report_pdf(output_stream: BytesIO, citations: list[dict], model_card_id: str = "unknown") -> None:
    """Generate a PDF citation report from validated citation data.

    This function creates a multi-page PDF with a title, timestamp, executive summary,
    and table of citations. The table auto-wraps long text and repeats headers on each page.
    All text is rendered using DejaVu Sans font to support Unicode characters.

    Args:
        output_stream: BytesIO stream to write the PDF to
        citations: List of citation dictionaries (pre-validated by citation_schema)
                   Each citation should have: question_id, question_text, answer,
                   source_quote, source_section, confidence, reasoning
        model_card_id: Model card identifier for footer and summary (default: "unknown")

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
        >>> generate_source_report_pdf(buf, [c.model_dump() for c in report.citations], model_card_id='meta-llama/Llama-3.1')
        >>> buf.seek(0)
        >>> pdf_bytes = buf.read()
    """
    # Create document with margins (increased bottom margin for footer)
    doc = SimpleDocTemplate(
        output_stream,
        pagesize=letter,
        topMargin=0.5 * inch,
        bottomMargin=0.75 * inch,
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

    # Add executive summary
    summary_flowables = _build_executive_summary(citations, model_card_id)
    story.extend(summary_flowables)

    # Add spacer before table
    story.append(Spacer(1, 0.3 * inch))

    # Build table data
    # Header row - updated to reflect new content structure
    headers = ['#', 'Question', 'Answer', 'Source/Details', 'Section', 'Confidence', 'Reasoning']
    header_row = [Paragraph(_escape_xml(h), header_text_style) for h in headers]

    # Data rows
    table_data = [header_row]
    for citation in citations:
        confidence = citation.get('confidence', '')
        question_id = citation.get('question_id', '')
        question_text = citation.get('question_text', '')
        answer = citation.get('answer', '')
        source_quote = citation.get('source_quote', '')
        source_section = citation.get('source_section', '')
        reasoning = citation.get('reasoning', '')

        # Format Source/Details column based on confidence level
        if confidence == 'DIRECT':
            source_details = f"<i>{_escape_xml(source_quote)}</i><br/><br/>Section: {_escape_xml(source_section)}"
        elif confidence == 'INFERRED':
            source_details = f"Related: <i>{_escape_xml(source_quote)}</i><br/><br/>Reasoning: {_escape_xml(reasoning)}"
        elif confidence == 'DEFAULT':
            source_details = f"Standard value applied.<br/><br/>Rationale: {_escape_xml(reasoning)}"
        elif confidence == 'NOT FOUND':
            source_details = f"Information not found.<br/><br/>Searched: {_escape_xml(reasoning)}"
        else:
            # Fallback for unknown confidence levels
            source_details = _escape_xml(source_quote)

        # Format section column (dash for DEFAULT/NOT FOUND)
        if confidence in ['DEFAULT', 'NOT FOUND']:
            section_display = '-'
        else:
            section_display = source_section

        row = [
            Paragraph(_escape_xml(question_id), cell_text_style),
            Paragraph(_escape_xml(question_text), cell_text_style),
            Paragraph(_escape_xml(answer), cell_text_style),
            Paragraph(source_details, cell_text_style),
            Paragraph(_escape_xml(section_display), cell_text_style),
            Paragraph(_escape_xml(confidence), cell_text_style),
            Paragraph(_escape_xml(reasoning), cell_text_style),
        ]
        table_data.append(row)

    # Create table with column widths
    col_widths = [
        0.3 * inch,  # #
        1.3 * inch,  # Question
        1.4 * inch,  # Answer
        2.0 * inch,  # Source Quote
        0.6 * inch,  # Section
        0.8 * inch,  # Confidence
        1.1 * inch,  # Reasoning
    ]

    table = Table(table_data, colWidths=col_widths, repeatRows=1, splitByRow=True)

    # Apply base table style
    style_commands = [
        # Header row styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A5568')),  # Dark grey
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),

        # Data rows styling
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('VALIGN', (0, 1), (-1, -1), 'TOP'),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),

        # Grid lines
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),

        # Padding
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]

    # Apply confidence-based row colors
    for idx, citation in enumerate(citations, start=1):
        confidence = citation.get('confidence', '')
        if confidence in CONFIDENCE_COLORS:
            bg_color = CONFIDENCE_COLORS[confidence]
            # Row index in table_data is idx (because header is row 0)
            style_commands.append(('BACKGROUND', (0, idx), (-1, idx), bg_color))

    table.setStyle(TableStyle(style_commands))

    story.append(table)

    # Create footer callback and build PDF
    footer_fn = _create_footer_callback(model_card_id)
    doc.build(story, onFirstPage=footer_fn, onLaterPages=footer_fn)
