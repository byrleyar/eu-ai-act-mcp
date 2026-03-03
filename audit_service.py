import json
import collections
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Literal, Optional

import anthropic
from pydantic import BaseModel

from compliance_service import ProcessingContext

# ---------------------------------------------------------------------------
# Score / Confidence type aliases
# ---------------------------------------------------------------------------

ScoreValue = Literal["1", "1i", "2", "3", "4"]
ConfidenceValue = Literal["DIRECT", "INFERRED", "DEFAULT", "NOT FOUND"]

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class FieldAudit(BaseModel):
    question_id: str
    answer: str
    score: ScoreValue
    score_label: str
    source_quote: str
    source_section: str
    confidence: ConfidenceValue
    reasoning: str


class AuditSummary(BaseModel):
    total_fields: int
    score_1_count: int
    score_1i_count: int
    score_2_count: int
    score_3_count: int
    score_4_count: int


class AuditResult(BaseModel):
    model_id: str
    audit_timestamp: str
    auditor_model: str
    summary: AuditSummary
    field_audits: List[FieldAudit]


# ---------------------------------------------------------------------------
# Prompt constants
# ---------------------------------------------------------------------------

AUDIT_SYSTEM_PROMPT = """You are a skeptical compliance auditor reviewing EU AI Act compliance documentation.

Your role is to audit every field in a compliance form by cross-referencing the answers against the provided model card evidence.

## Scoring Rubric

Assign a score to each field using ONLY the following values:

1 = Accurate (matches model card) — The answer is directly supported by the model card. You MUST provide a direct quote.
1i = Accurate - reasonably inferred (correct answer derived from indirect evidence) — The answer is correct but required inference from related information. Explain your reasoning.
2 = Inaccurate/Hallucinated (asserts something not in or contradicted by model card) — The answer makes a claim that is not present in or is contradicted by the model card.
3 = Incomplete (misses information present in model card) — The answer omits information that is clearly present in the model card.
4 = Appropriately Unavailable (correctly indicates info not available when model card lacks it) — The answer correctly states the information is not available and the model card indeed lacks it.

## Critical Rules

- Assume hallucinations may have occurred. Be skeptical of specific numbers, dates, and claims.
- Score 1 only when you can provide a direct quote from the model card that supports the answer.
- Score 1i when the answer is correct but requires reasonable inference. Explain your reasoning.
- Score 2 when the answer asserts something not in the model card or contradicts it.
- Score 3 when the answer omits material information that IS present in the model card.
- Score 4 when the answer correctly says "N/A" or "not available" AND the model card genuinely lacks that information.
- You MUST return exactly one entry per question_id. Do not skip any question.
- Valid score values are ONLY: 1, 1i, 2, 3, 4 — no other values are acceptable.
- If you realize you may have hallucinated or overstated something, flag it honestly.

## Output Format

Return a JSON array (and ONLY a JSON array — no markdown fences, no preamble, no trailing text).

Each element must be a JSON object with exactly these fields:
{
  "question_id": "string — the question ID from the questions list",
  "answer": "string — the answer that was given in the compliance form",
  "score": "string — one of: 1, 1i, 2, 3, 4",
  "score_label": "string — human-readable label matching the score (e.g. 'Accurate', 'Accurate - reasonably inferred', 'Inaccurate/Hallucinated', 'Incomplete', 'Appropriately Unavailable')",
  "source_quote": "string — exact quote from model card (empty string if score is 2, 3, or 4)",
  "source_section": "string — section heading where quote was found (empty string if not applicable)",
  "confidence": "string — one of: DIRECT, INFERRED, DEFAULT, NOT FOUND",
  "reasoning": "string — brief explanation of why you assigned this score"
}
"""

COMPLIANCE_SYSTEM_PROMPT = """You are a compliance form assistant filling in an EU AI Act compliance questionnaire.

Read the provided model card carefully and answer each question based ONLY on information present in the model card.
If information is not available in the model card, respond with "Not available in model card."

## Output Format

Return a JSON object (and ONLY a JSON object — no markdown fences, no preamble, no trailing text) where each key is a question_id and each value is the answer string:

{"question_id": "answer", ...}
"""

# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------


def build_audit_user_prompt(model_card_text: str, questions: list, compliance_data: dict = None) -> str:
    """Constructs the user message for the audit LLM call."""
    if compliance_data:
        # Embed pre-filled answers alongside each question so Opus scores existing answers
        enriched = [
            {**q, "pre_filled_answer": compliance_data.get(q["id"], "Not provided")}
            for q in questions
        ]
        questions_json = json.dumps(enriched, indent=2)
        audit_instruction = "Each question includes a pre_filled_answer. Score that answer against the model card — do NOT re-derive answers."
    else:
        questions_json = json.dumps(questions, indent=2)
        audit_instruction = "The compliance form was filled in using ONLY the model card above. Audit every answer."
    return f"""## MODEL CARD

{model_card_text}

## QUESTIONS TO ANSWER AND AUDIT

{audit_instruction}

{questions_json}

Audit each question_id listed above. Return a JSON array with one object per question_id, following the format in the system prompt exactly.
"""


def build_compliance_user_prompt(model_card_text: str, questions: list) -> str:
    """Constructs the user message for the Sonnet compliance form-filling call."""
    question_items = "\n".join(
        f'- {q["id"]}: {q["question"]}' for q in questions
    )
    return f"""## MODEL CARD

{model_card_text}

## QUESTIONS

Answer each question using ONLY the model card above. Return a JSON object mapping question_id to answer string.

{question_items}
"""


# ---------------------------------------------------------------------------
# AuditService
# ---------------------------------------------------------------------------


class AuditService:
    """Reads model card, calls Anthropic API to audit compliance fields, persists results."""

    def __init__(self, anthropic_client=None):
        if anthropic_client is not None:
            self.client = anthropic_client
        else:
            self.client = anthropic.Anthropic()

    def generate_compliance_data(self, ctx: ProcessingContext) -> dict:
        """
        Call Sonnet (no extended thinking) to fill in compliance answers from the model card.
        Saves compliance_data.json to ctx.output_path and returns the {question_id: answer} dict.
        """
        model_card_path = Path(ctx.output_path) / "model_card.txt"
        model_card_text = model_card_path.read_text(encoding="utf-8")

        questions_path = Path(__file__).parent / "questions.json"
        with open(questions_path, "r", encoding="utf-8") as f:
            questions = json.load(f)

        user_prompt = build_compliance_user_prompt(model_card_text, questions)

        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8000,
            system=COMPLIANCE_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        raw_text = response.content[0].text.strip()
        # Handle optional markdown fences
        if raw_text.startswith("```"):
            first_newline = raw_text.find("\n")
            if first_newline != -1:
                raw_text = raw_text[first_newline + 1:]
            if raw_text.rstrip().endswith("```"):
                raw_text = raw_text.rstrip()[:-3].rstrip()

        compliance_data = json.loads(raw_text)

        output_path = Path(ctx.output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        with open(output_path / "compliance_data.json", "w", encoding="utf-8") as f:
            json.dump(compliance_data, f, indent=2)

        return compliance_data

    def audit_model(self, ctx: ProcessingContext) -> AuditResult:
        """
        Audit compliance fields for a model:
        1. Call generate_compliance_data() (Sonnet) if compliance_data.json absent
        2. Load compliance_data.json
        3. Build prompts with pre-filled answers embedded
        4. Call Opus + extended thinking to score each answer
        5. Persist audit_results.json
        6. Return AuditResult
        """
        output_path = Path(ctx.output_path)

        # ---- 1. Read model card ----
        model_card_path = output_path / "model_card.txt"
        if not model_card_path.exists():
            raise FileNotFoundError(
                f"model_card.txt not found at {model_card_path}. "
                "Run the batch processor first to fetch model cards."
            )
        model_card_text = model_card_path.read_text(encoding="utf-8")

        # ---- 2. Load questions ----
        questions_path = Path(__file__).parent / "questions.json"
        with open(questions_path, "r", encoding="utf-8") as f:
            questions = json.load(f)

        # ---- 3. Generate or load compliance_data ----
        compliance_data_path = output_path / "compliance_data.json"
        if not compliance_data_path.exists():
            compliance_data = self.generate_compliance_data(ctx)
        else:
            with open(compliance_data_path, "r", encoding="utf-8") as f:
                compliance_data = json.load(f)

        # ---- 4. Build prompts ----
        system_prompt = AUDIT_SYSTEM_PROMPT
        user_prompt = build_audit_user_prompt(model_card_text, questions, compliance_data)

        # ---- 5. Call Anthropic API (Opus + extended thinking) ----
        response = self.client.messages.create(
            model="claude-opus-4-6",
            max_tokens=16000,
            thinking={"type": "enabled", "budget_tokens": 10000},
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        # With extended thinking enabled, find the text block by type.
        text_block = next(b for b in response.content if b.type == "text")
        raw_text = text_block.text

        # ---- 6. Extract JSON (handle markdown code fences) ----
        text = raw_text.strip()
        if text.startswith("```"):
            first_newline = text.find("\n")
            if first_newline != -1:
                text = text[first_newline + 1:]
            if text.rstrip().endswith("```"):
                text = text.rstrip()[:-3].rstrip()

        parsed = json.loads(text)

        # ---- 7. Validate each entry as FieldAudit ----
        field_audits: List[FieldAudit] = [FieldAudit(**entry) for entry in parsed]

        # ---- 8. Validate count matches questions ----
        if len(field_audits) != len(questions):
            raise ValueError(
                f"Audit response has {len(field_audits)} entries but "
                f"{len(questions)} questions were expected. "
                "The LLM may have skipped or duplicated entries."
            )

        # ---- 9. Build AuditSummary ----
        score_counts = collections.Counter(fa.score for fa in field_audits)
        summary = AuditSummary(
            total_fields=len(field_audits),
            score_1_count=score_counts.get("1", 0),
            score_1i_count=score_counts.get("1i", 0),
            score_2_count=score_counts.get("2", 0),
            score_3_count=score_counts.get("3", 0),
            score_4_count=score_counts.get("4", 0),
        )

        # ---- 10. Build AuditResult ----
        audit_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        result = AuditResult(
            model_id=ctx.model_id,
            audit_timestamp=audit_timestamp,
            auditor_model="claude-opus-4-6",
            summary=summary,
            field_audits=field_audits,
        )

        # ---- 11. Persist audit_results.json ----
        output_path.mkdir(parents=True, exist_ok=True)
        with open(output_path / "audit_results.json", "w", encoding="utf-8") as f:
            json.dump(result.model_dump(), f, indent=2)

        return result
