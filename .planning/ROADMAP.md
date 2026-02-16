# Roadmap: EU AI Act Compliance MCP Server

## Milestones

- SHIPPED **v1.1 Source Citation Reports** -- Phases 1-3 (shipped 2026-02-15)
- IN PROGRESS **v1.2 Source Report Reliability** -- Phases 4-6

## Phases

<details>
<summary>v1.1 Source Citation Reports (Phases 1-3) -- SHIPPED 2026-02-15</summary>

- [x] Phase 1: PDF Infrastructure & Data Model (2/2 plans) -- completed 2026-02-15
- [x] Phase 2: MCP Tool Integration & File Management (2/2 plans) -- completed 2026-02-15
- [x] Phase 3: Citation Features & Workflow (4/4 plans) -- completed 2026-02-15

See [v1.1-ROADMAP.md](milestones/v1.1-ROADMAP.md) for full details.

</details>

### v1.2 Source Report Reliability

**Milestone Goal:** Make source citation reports trustworthy by ensuring full coverage, detecting hallucinations, and automating the generation flow.

- [ ] **Phase 4: Hallucination Detection** - Schema and PDF rendering for the HALLUCINATED confidence level
- [ ] **Phase 5: Coverage Enforcement** - Validate all 80 questions are present in source reports
- [ ] **Phase 6: Workflow & Instructions** - context.md overhaul for self-verification, coverage, and automation

## Phase Details

### Phase 4: Hallucination Detection
**Goal**: Users can see which compliance answers are not supported by model card sources, with clear visual warning in the PDF report
**Depends on**: Phase 3 (v1.1 baseline)
**Requirements**: HALL-01, HALL-02, HALL-04
**Success Criteria** (what must be TRUE):
  1. HALLUCINATED is a valid confidence level in the citation schema alongside DIRECT, INFERRED, DEFAULT, and NOT FOUND
  2. PDF report renders HALLUCINATED citations in bold red with distinct visual treatment that stands out from all other confidence levels
  3. Executive summary at the top of the PDF includes HALLUCINATED count in the confidence breakdown (e.g., "HALLUCINATED: 3")
  4. Existing tests continue to pass -- no regression in DIRECT, INFERRED, DEFAULT, or NOT FOUND handling
**Plans**: TBD

Plans:
- [ ] 04-01: TBD
- [ ] 04-02: TBD

### Phase 5: Coverage Enforcement
**Goal**: The generate_source_report tool guarantees every question in questions.json has a citation entry, rejecting incomplete reports
**Depends on**: Phase 4
**Requirements**: COV-01, COV-02
**Success Criteria** (what must be TRUE):
  1. Calling generate_source_report with citation JSON covering all 80 question IDs succeeds and produces a PDF with 80 citation entries
  2. Calling generate_source_report with citation JSON missing any question IDs returns a clear error listing the specific missing IDs
  3. The validation uses the authoritative questions.json as the source of truth for which IDs must be present
**Plans**: TBD

Plans:
- [ ] 05-01: TBD

### Phase 6: Workflow & Instructions
**Goal**: context.md instructs Claude to self-verify answers, include all 80 questions, and reliably execute the two-step tool sequence presenting both document links
**Depends on**: Phase 4, Phase 5
**Requirements**: HALL-03, COV-03, COV-04, WORK-01, WORK-02
**Success Criteria** (what must be TRUE):
  1. context.md contains explicit instructions for Claude to re-verify each answer against model card sources before building citation JSON, flagging unsupported claims as HALLUCINATED
  2. context.md lists all 80 question IDs so Claude knows the complete set to include in citation JSON
  3. context.md instructs Claude to create NOT FOUND citations with reasoning for any questions not addressed in the compliance form
  4. context.md defines a clear two-step tool sequence (generate_compliance_doc then generate_source_report) with stronger enforcement language than v1.1
  5. context.md instructs Claude to present both the DOCX compliance form link and PDF source citation report link together in the final response
**Plans**: TBD

Plans:
- [ ] 06-01: TBD

## Progress

**Execution Order:** Phase 4 -> Phase 5 -> Phase 6

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|---------------|--------|-----------|
| 1. PDF Infrastructure & Data Model | v1.1 | 2/2 | Complete | 2026-02-15 |
| 2. MCP Tool Integration & File Management | v1.1 | 2/2 | Complete | 2026-02-15 |
| 3. Citation Features & Workflow | v1.1 | 4/4 | Complete | 2026-02-15 |
| 4. Hallucination Detection | v1.2 | 0/? | Not started | - |
| 5. Coverage Enforcement | v1.2 | 0/? | Not started | - |
| 6. Workflow & Instructions | v1.2 | 0/? | Not started | - |

---
*Roadmap created: 2026-02-15*
*Last updated: 2026-02-16 after v1.2 roadmap created*
