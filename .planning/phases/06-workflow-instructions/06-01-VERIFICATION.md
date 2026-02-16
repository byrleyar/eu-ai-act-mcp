# Phase 06 Plan 01 Verification

## Manual Checklist

### 1. Content Verification
- [ ] `HALLUCINATED` is defined in the confidence level section.
- [ ] Strict 2-step tool sequence is clearly explained.
- [ ] Requirement to include all 80+ IDs is prominent.
- [ ] Both links presentation rule is included.
- [ ] The ID list in `context.md` matches `questions.json`.

### 2. Execution Roleplay (Simulated)
**Scenario**: Model card found, but doesn't mention "energy consumption".
**Expected Claude Behavior (per new instructions)**:
1. Answers "N/A" for energy consumption in DOCX.
2. In PDF source report, creates a `NOT FOUND` citation for `energy_used`.
3. Calls both tools.
4. Returns both links.

### 3. Hallucination Roleplay (Simulated)
**Scenario**: Claude accidentally "guesses" the training time as 3 months when it's not in the card.
**Expected Claude Behavior (per new instructions)**:
1. Re-verifies answer during citation drafting.
2. Realizes it's a guess.
3. Flags it as `HALLUCINATED` in the source report.
