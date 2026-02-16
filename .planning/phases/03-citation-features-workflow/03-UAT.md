---
status: diagnosed
phase: 03-citation-features-workflow
source: [03-01-SUMMARY.md, 03-02-SUMMARY.md]
started: 2026-02-15T15:00:00Z
updated: 2026-02-15T15:25:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Executive Summary in PDF
expected: Generate a PDF with the `generate_source_report` tool. The first page shows an "Executive Summary" section with model card ID, total questions, and confidence breakdown (count + percentage per level).
result: pass

### 2. Confidence-Based Row Coloring
expected: In the generated PDF, citation rows have distinct background colors by confidence level: green-ish for DIRECT, yellow-ish for INFERRED, gray for DEFAULT, red-ish for NOT FOUND. Colors should be distinguishable even without reading the text label.
result: pass

### 3. DIRECT Citation Formatting
expected: A DIRECT confidence citation shows the source quote in italics with section attribution (e.g., "Section: Architecture"). The verbatim quote should be visually distinct from other text.
result: issue
reported: "the quotes are not in italics. also, the source needs to include the source document, not just the section. this tool pulls from the model card and also attached pdfs. it could also be given additional context from the user. the source document must be included in addition to the location in the document"
severity: major

### 4. NOT FOUND Citation Formatting
expected: A NOT FOUND citation shows "Information not found" with reasoning explaining what was searched for. The answer field may be empty. It should be clear this is missing information, not an error.
result: pass

### 5. Page Footer with Metadata
expected: Every page of the PDF has a footer showing the model card identifier on the left and generation timestamp + page number on the right. Footer appears in small gray text at the bottom.
result: pass

### 6. Question ID Cross-Referencing
expected: The first column of the citation table shows question IDs (e.g., "model_architecture") instead of sequential row numbers. These IDs match the question IDs used in the compliance form.
result: pass

### 7. Citation Tracking Instructions in context.md
expected: context.md contains a "Citation Tracking" section that instructs Claude to: (1) track sources with confidence levels while filling out the compliance form, (2) call generate_source_report immediately after generate_compliance_doc, (3) include model_card_id parameter. A JSON example with all 7 citation fields is provided.
result: pass

### 8. All Tests Pass
expected: Running `python -m pytest tests/ -v` passes all 54 tests (15 citation schema + 23 PDF generator + 16 source report tool) with zero failures.
result: pass

## Summary

total: 8
passed: 7
issues: 1
pending: 0
skipped: 0

## Gaps

- truth: "DIRECT citations show source quote in italics with section attribution"
  status: failed
  reason: "User reported: quotes are not in italics. Source needs to include the source document, not just the section. Tool pulls from model card and attached PDFs and user context. Source document must be included."
  severity: major
  test: 3
  root_cause: "Two separate issues: (1) Only DejaVuSans.ttf (regular) is registered — no italic font variant exists in fonts/ directory, so ReportLab silently falls back to regular weight when <i> tags are used. (2) Citation schema has source_section but no source_document field — cannot track which document (model card, PDF attachment, user context) contained the quote."
  artifacts:
    - path: "pdf_generator.py"
      issue: "Line 28 registers only regular font. No registerFontFamily() call for italic mapping."
    - path: "citation_schema.py"
      issue: "Citation model (lines 26-51) has source_section but no source_document field."
    - path: "context.md"
      issue: "Citation tracking instructions and JSON example lack source_document field."
  missing:
    - "Download DejaVuSans-Oblique.ttf to fonts/ directory"
    - "Register italic font variant with pdfmetrics.registerFont and registerFontFamily"
    - "Add source_document field to Citation Pydantic model in citation_schema.py"
    - "Update PDF formatter to display source_document in citation rows"
    - "Update context.md example and instructions to include source_document"
  debug_session: ""

- truth: "Table layout is readable with appropriately sized text and balanced column widths"
  status: failed
  reason: "User reported: table format is off, text is too big. Question IDs in # column break across 7+ lines. Column widths are unbalanced."
  severity: major
  test: 5
  root_cause: "# column width is 0.3 inches (4% of page width) — supports only ~7-9 chars at 8pt font. Question IDs like 'model_architecture' (17 chars) and 'training_data_sources' (21 chars) need 0.7-0.8 inch minimum. Columns are inversely proportioned to content: Section column (0.6 inch) is oversized for short refs while # column is critically undersized."
  artifacts:
    - path: "pdf_generator.py"
      issue: "Lines 282-290: column widths hardcoded. # is 0.3*inch, Section is 0.6*inch. Current distribution: # 4%, Question 17%, Answer 19%, Source 27%, Section 8%, Confidence 11%, Reasoning 15%."
  missing:
    - "Rebalance column widths: # from 0.3 to 0.7 inch, Section from 0.6 to 0.5, Source from 2.0 to 1.8, Question from 1.3 to 1.2, Answer from 1.4 to 1.3"
  debug_session: ".planning/debug/pdf-table-layout.md"
