# Roadmap: EU AI Act Compliance MCP Server

## Milestones

- SHIPPED **v1.1 Source Citation Reports** -- Phases 1-3 (shipped 2026-02-15)
- SHIPPED **v1.2 Source Report Reliability** -- Phases 4-6 (shipped 2026-02-16)
- SHIPPED **v1.3 High-Fidelity Data Acquisition** -- Phases 7-9 (shipped 2026-02-16)
- IN PROGRESS **v1.4 Automated Batch Testing & Compliance Audit** -- Phases 11-13 (started 2026-03-02)

## Phases

<details>
<summary>v1.1 Source Citation Reports (Phases 1-3) -- SHIPPED 2026-02-15</summary>

- [x] Phase 1: PDF Infrastructure & Data Model (2/2 plans) -- completed 2026-02-15
- [x] Phase 2: MCP Tool Integration & File Management (2/2 plans) -- completed 2026-02-15
- [x] Phase 3: Citation Features & Workflow (4/4 plans) -- completed 2026-02-15

</details>

<details>
<summary>v1.2 Source Report Reliability (Phases 4-6) -- SHIPPED 2026-02-16</summary>

- [x] Phase 4: Hallucination Detection (1/1 plans) -- completed 2026-02-16
- [x] Phase 5: Coverage Enforcement (1/1 plans) -- completed 2026-02-16
- [x] Phase 6: Workflow & Instructions (1/1 plans) -- completed 2026-02-16

</details>

<details>
<summary>v1.3 High-Fidelity Data Acquisition (Phases 7-9) -- SHIPPED 2026-02-16</summary>

- [x] Phase 7: Discovery Engine (1/1 plans) -- completed 2026-02-16
- [x] Phase 8: Targeted Fetch Tool (1/1 plans) -- completed 2026-02-16
- [x] Phase 9: Agentic Retrieval Workflow (1/1 plans) -- completed 2026-02-16

</details>

<details>
<summary>Post-v1.3 Fixes (Phase 10) -- SHIPPED 2026-02-16</summary>

- [x] Phase 10: Fix Source Report Layout and Document Attribution (1/1 plans) -- completed 2026-02-16

</details>

## Progress

**Milestone v1.4 IN PROGRESS**

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|---------------|--------|-----------|
| 1. PDF Infrastructure & Data Model | v1.1 | 2/2 | Complete | 2026-02-15 |
| 2. MCP Tool Integration & File Management | v1.1 | 2/2 | Complete | 2026-02-15 |
| 3. Citation Features & Workflow | v1.1 | 4/4 | Complete | 2026-02-15 |
| 4. Hallucination Detection | v1.2 | 1/1 | Complete | 2026-02-16 |
| 5. Coverage Enforcement | v1.2 | 1/1 | Complete | 2026-02-16 |
| 6. Workflow & Instructions | v1.2 | 1/1 | Complete | 2026-02-16 |
| 7. Discovery Engine | v1.3 | 1/1 | Complete | 2026-02-16 |
| 8. Targeted Fetch Tool | v1.3 | 1/1 | Complete | 2026-02-16 |
| 9. Agentic Retrieval Workflow | v1.3 | 1/1 | Complete | 2026-02-16 |
| 10. Fix Source Report Layout & Attribution | Post-v1.3 | 1/1 | Complete | 2026-02-16 |
| 11. Batch Processing Engine | v1.4 | 1/1 | Complete | 2026-03-02 |
| 12. Automated Audit Workflow | v1.4 | 2/2 | Complete | 2026-03-02 |

- [x] Phase 11: Batch Processing Engine (1/1 plans) -- completed 2026-03-02
- [x] Phase 12: Automated Audit Workflow (2/2 plans) -- completed 2026-03-02
- [ ] Phase 13: Aggregate Results & Reporting

**Goal:** Compile individual audit results into a master summary report (Excel/CSV).
**Depends on:** Phase 12
**Requirements:** REP-01, REP-02, REP-03
**Plans:** 2 plans
Plans:
- [ ] 13-01-PLAN.md -- ReportGenerator core (SECTION_MAP, metrics, CSV, unit tests)
- [ ] 13-02-PLAN.md -- Excel workbook generation (3 sheets) and end-to-end validation

**Success Criteria:**
1. A single summary table is generated showing accuracy metrics across all models in a batch.
2. The summary matches the requested hackathon validation format.
3. An executive summary provides high-level findings.

---
*Roadmap updated: 2026-03-02 for Milestone v1.4*
