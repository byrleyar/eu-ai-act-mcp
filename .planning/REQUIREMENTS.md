# Requirements: Source Report Reliability

**Defined:** 2026-02-16
**Core Value:** Every answer in the compliance document must be traceable back to its source.

## v1.2 Requirements

Requirements for v1.2 release. Each maps to roadmap phases.

### Hallucination Detection

- [ ] **HALL-01**: HALLUCINATED confidence level added to citation schema as 5th enum value alongside DIRECT, INFERRED, DEFAULT, NOT FOUND
- [ ] **HALL-02**: PDF renders HALLUCINATED citations with distinct color and formatting (bold red warning, clear visual distinction from other confidence levels)
- [ ] **HALL-03**: context.md instructs Claude to re-verify each answer against model card sources before building citation JSON, flagging unsupported claims as HALLUCINATED
- [ ] **HALL-04**: Executive summary includes HALLUCINATED count in confidence breakdown statistics

### Workflow Automation

- [ ] **WORK-01**: context.md restructured with explicit two-step tool sequence (generate_compliance_doc then generate_source_report) with stronger enforcement language ensuring reliable automatic execution
- [ ] **WORK-02**: Both document links (DOCX compliance form + PDF source citation report) presented together in Claude's final response to user

### Coverage Completeness

- [ ] **COV-01**: Source report contains a citation entry for every question in questions.json (all 80 questions)
- [ ] **COV-02**: generate_source_report tool validates that all question IDs from questions.json are present in the citation JSON, returning a clear error listing missing IDs if any are absent
- [ ] **COV-03**: context.md provides the full list of 80 question IDs so Claude knows exactly which entries to include in the citation JSON
- [ ] **COV-04**: Questions not addressed in the compliance form appear as NOT FOUND citations with reasoning explaining the coverage gap

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Enhanced Citation Features

- **CITE-10**: Page/section references for faster source verification in large documents
- **CITE-11**: Highlighting of key phrases within source quotes
- **CITE-12**: Negative evidence tracking -- document what was searched but NOT found
- **CITE-13**: Regulatory mapping -- link each question to specific EU AI Act articles

### Advanced Features

- **ADV-01**: Multi-source reconciliation when answer comes from conflicting sources
- **ADV-02**: Change tracking across multiple versions of the compliance form
- **ADV-03**: Auditor annotation space (margins or comment fields for reviewer notes)
- **ADV-04**: Alternative interpretation flags for ambiguous source material

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Modifying existing DOCX template | Not needed -- separate PDF report |
| Embedding citations in DOCX | Separate PDF is cleaner |
| Real-time validation during form fill | Source report is post-generation |
| Automatic confidence boosting | Creates audit risk -- humans must verify |
| PDF/A archival format | Verify regulatory requirements first |
| Server-side hallucination detection | Detection happens in Claude's reasoning, not in Python code |
| Modifying questions.json content | Question definitions are stable -- only coverage enforcement changes |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| HALL-01 | Phase 4 | Pending |
| HALL-02 | Phase 4 | Pending |
| HALL-03 | Phase 6 | Pending |
| HALL-04 | Phase 4 | Pending |
| WORK-01 | Phase 6 | Pending |
| WORK-02 | Phase 6 | Pending |
| COV-01 | Phase 5 | Pending |
| COV-02 | Phase 5 | Pending |
| COV-03 | Phase 6 | Pending |
| COV-04 | Phase 6 | Pending |

**Coverage:**
- v1.2 requirements: 10 total
- Mapped to phases: 10
- Unmapped: 0

**Phase distribution:**
- Phase 4 (Hallucination Detection): HALL-01, HALL-02, HALL-04 (3 requirements)
- Phase 5 (Coverage Enforcement): COV-01, COV-02 (2 requirements)
- Phase 6 (Workflow & Instructions): HALL-03, COV-03, COV-04, WORK-01, WORK-02 (5 requirements)

---
*Requirements defined: 2026-02-16*
*Last updated: 2026-02-16 after v1.2 roadmap created*
