# Milestones

## v1.1 Source Citation Reports — SHIPPED 2026-02-15

**Phases:** 1-3 (8 plans, 15 tasks)
**Requirements:** 25/25 complete
**Tests:** 57 passing
**LOC:** 2,279 Python

**Delivered:** PDF-based source citation reporting for the EU AI Act compliance MCP server, enabling audit trail traceability for every compliance form answer.

**Key Accomplishments:**
1. Pydantic citation data model with 4 confidence levels and field-path error formatting
2. ReportLab PDF generator with DejaVu Sans Unicode font, auto-wrapping tables, multi-page support
3. `generate_source_report` MCP tool with 24-hour file lifecycle management
4. WCAG AA compliant confidence coloring, executive summary, audit-ready page footers
5. Citation tracking workflow in context.md with confidence definitions and JSON examples
6. 57 passing tests covering all 25 requirements across 3 phases

**Git Range:** `fbec87e` (feat(01-01)) → `79b177f` (docs(03-03))

**Archives:**
- [v1.1-ROADMAP.md](milestones/v1.1-ROADMAP.md)
- [v1.1-REQUIREMENTS.md](milestones/v1.1-REQUIREMENTS.md)

## v1.2 Source Report Reliability — SHIPPED 2026-02-16

**Phases:** 4-6 (3 plans)
**Requirements:** 10/10 complete

**Delivered:** Server-side enforcement of source citations for all 80+ compliance questions, with automatic end-to-end workflow and a new HALLUCINATED confidence level.

**Key Accomplishments:**
1. HALLUCINATED confidence level with red coloring for answers contradicted by the source material
2. Automatic end-to-end workflow generating compliance doc and source report together
3. Mandatory server-side citation validation for all 80+ compliance questions
4. Coverage enforcement guarantees report completeness regardless of LLM behavior

**Archives:**
- [v1.2-ROADMAP.md](milestones/v1.2-ROADMAP.md)
- [v1.2-REQUIREMENTS.md](milestones/v1.2-REQUIREMENTS.md)

## v1.3 High-Fidelity Data Acquisition — SHIPPED 2026-02-16

**Phases:** 7-10 (4 plans)
**Requirements:** 8/8 complete
**LOC:** 3,100+ Python, 77 tests passing

**Delivered:** Targeted discovery and retrieval of technical documentation to fill compliance data gaps, shifting from "fetch everything" to an agentic "discover gaps, then fetch" loop.

**Key Accomplishments:**
1. Discovery Engine overhaul: automated extraction of links from BibTeX, citation blocks, and repo file lists
2. `fetch_external_document` MCP tool for on-demand retrieval and parsing of academic papers with SSRF protection
3. Agentic Retrieval Workflow (Gap Analysis → Targeted Fetch) for higher-fidelity compliance reports
4. Extended INFERRED citations to show document and section attribution matching DIRECT citation format

**Archives:**
- [v1.3-ROADMAP.md](milestones/v1.3-ROADMAP.md)
- [v1.3-REQUIREMENTS.md](milestones/v1.3-REQUIREMENTS.md)

## v1.4 Automated Batch Testing & Compliance Audit — SHIPPED 2026-03-02

**Phases:** 11-14 (6 plans)
**Requirements:** 14/14 complete
**Tests:** 39 new (117 total passing), 4,950 LOC Python

**Delivered:** End-to-end batch pipeline that processes multiple HuggingFace models, runs a Skeptical Auditor against each compliance form, and produces hackathon-format aggregate reports.

**Key Accomplishments:**
1. `ComplianceService` service layer extracted from server.py — reused by both MCP server and batch CLI
2. `batch_processor.py` CLI: process model lists from CSV/args, per-model state isolation, fault-tolerant loop with rich progress bars
3. `AuditService` with LLM Skeptical Auditor persona scoring all 80 answers on 1/1i/2/3/4 rubric, detecting hallucinations and data gaps
4. `audit_processor.py` CLI discovers batch directories and runs AuditService per model, generating `audit_summary.csv`
5. `ReportGenerator` producing hackathon-format `batch_report.xlsx` (3-sheet color-coded) + `batch_report.csv` + `executive_summary.txt`
6. Tech debt closure: stub test fixed, stale imports removed from server.py, portable paths, missing VERIFICATION.md created

**Git Range:** `e31fbb9` (feat(11-01)) → `2957f6e` (fix(14-01))

**Archives:**
- [v1.4-ROADMAP.md](milestones/v1.4-ROADMAP.md)
- [v1.4-REQUIREMENTS.md](milestones/v1.4-REQUIREMENTS.md)
- [v1.4-MILESTONE-AUDIT.md](milestones/v1.4-MILESTONE-AUDIT.md)

---


## v1.5 Analytical Reporting — SHIPPED 2026-03-03

**Phases:** 15 (1 phase, 2 plans, 4 tasks)
**LOC:** 6,729 Python total (1,337 added — generate_report.py)

**Delivered:** Publication-ready Markdown analytical report (`batch_report.md`) generated from batch `audit_results.json` files, with 8 statistical tables, auto-generated data-derived commentary, and 9 CSV exports per batch run.

**Key Accomplishments:**
1. `generate_report.py` CLI with 4-stage pipeline (Load → Join → Aggregate → Render) using Typer + pandas
2. Tables 1-4: aggregate summary stats, per-model detail, by org type, by domain breakdown — with CSV exports
3. `combined_field_audits.csv` — raw question-level data across all models for downstream analysis
4. Tables 5-8: section N/A rates, org-type breakdown with 15pp deviation highlighting, hallucinated/incomplete question rankings
5. `assemble_report()` — complete `batch_report.md` with data-derived auto-commentary naming actual values (top section, accuracy range, problem questions)
6. 10 output files per batch run; smoke assertions in `run()` for fail-fast validation

**Git Range:** `f3049fc` (feat(15-01)) → `8114fae` (feat(15-02))

**Archives:**
- [v1.5-ROADMAP.md](milestones/v1.5-ROADMAP.md)

---
