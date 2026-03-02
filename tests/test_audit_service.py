"""
Unit tests for audit_service.py.

Tests cover Pydantic model validation, score/confidence constraints,
AuditSummary construction, AuditResult serialization, prompt content,
and score distribution math -- WITHOUT calling the actual Anthropic API.
"""

import collections
import json

import pytest
from pydantic import ValidationError

from audit_service import (
    AUDIT_SYSTEM_PROMPT,
    AuditResult,
    AuditSummary,
    FieldAudit,
    build_audit_user_prompt,
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def make_field_audit(
    question_id: str = "test_q",
    answer: str = "test answer",
    score: str = "1",
    score_label: str = "Accurate",
    source_quote: str = "Direct quote from model card",
    source_section: str = "Model Details",
    confidence: str = "DIRECT",
    reasoning: str = "Directly stated in model card",
) -> FieldAudit:
    """Build a FieldAudit with sensible defaults for concise tests."""
    return FieldAudit(
        question_id=question_id,
        answer=answer,
        score=score,
        score_label=score_label,
        source_quote=source_quote,
        source_section=source_section,
        confidence=confidence,
        reasoning=reasoning,
    )


def make_summary(
    total_fields: int = 5,
    score_1_count: int = 2,
    score_1i_count: int = 1,
    score_2_count: int = 0,
    score_3_count: int = 1,
    score_4_count: int = 1,
) -> AuditSummary:
    return AuditSummary(
        total_fields=total_fields,
        score_1_count=score_1_count,
        score_1i_count=score_1i_count,
        score_2_count=score_2_count,
        score_3_count=score_3_count,
        score_4_count=score_4_count,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestFieldAuditScores:
    def test_field_audit_valid_scores(self):
        """All 5 valid score values should construct without error."""
        for score in ("1", "1i", "2", "3", "4"):
            fa = make_field_audit(score=score)
            assert fa.score == score

    def test_field_audit_invalid_score_five(self):
        """Score '5' must raise ValidationError."""
        with pytest.raises(ValidationError):
            make_field_audit(score="5")

    def test_field_audit_invalid_score_string(self):
        """Score 'invalid' must raise ValidationError."""
        with pytest.raises(ValidationError):
            make_field_audit(score="invalid")


class TestFieldAuditConfidence:
    def test_field_audit_confidence_values(self):
        """All 4 valid confidence values should construct without error."""
        for confidence in ("DIRECT", "INFERRED", "DEFAULT", "NOT FOUND"):
            fa = make_field_audit(confidence=confidence)
            assert fa.confidence == confidence

    def test_field_audit_invalid_confidence(self):
        """An unrecognised confidence value must raise ValidationError."""
        with pytest.raises(ValidationError):
            make_field_audit(confidence="UNKNOWN")


class TestAuditSummary:
    def test_audit_summary_counts(self):
        """AuditSummary stores each count correctly."""
        summary = AuditSummary(
            total_fields=10,
            score_1_count=4,
            score_1i_count=2,
            score_2_count=1,
            score_3_count=2,
            score_4_count=1,
        )
        assert summary.total_fields == 10
        assert summary.score_1_count == 4
        assert summary.score_1i_count == 2
        assert summary.score_2_count == 1
        assert summary.score_3_count == 2
        assert summary.score_4_count == 1


class TestAuditResult:
    def _make_result(self) -> AuditResult:
        audits = [
            make_field_audit(question_id="q1", score="1"),
            make_field_audit(question_id="q2", score="1i", confidence="INFERRED"),
            make_field_audit(question_id="q3", score="4", confidence="NOT FOUND"),
        ]
        summary = AuditSummary(
            total_fields=3,
            score_1_count=1,
            score_1i_count=1,
            score_2_count=0,
            score_3_count=0,
            score_4_count=1,
        )
        return AuditResult(
            model_id="org/model-name",
            audit_timestamp="2026-03-02T10:00:00Z",
            auditor_model="claude-sonnet-4-20250514",
            summary=summary,
            field_audits=audits,
        )

    def test_audit_result_construction(self):
        """AuditResult correctly stores model_id, timestamp, auditor_model, summary, field_audits."""
        result = self._make_result()
        assert result.model_id == "org/model-name"
        assert result.audit_timestamp == "2026-03-02T10:00:00Z"
        assert result.auditor_model == "claude-sonnet-4-20250514"
        assert result.summary.total_fields == 3
        assert result.summary.score_1_count == 1
        assert result.summary.score_1i_count == 1
        assert result.summary.score_4_count == 1
        assert len(result.field_audits) == 3

    def test_audit_result_serialization(self):
        """model_dump() produces a dict with expected top-level keys; json.dumps produces valid JSON."""
        result = self._make_result()
        dumped = result.model_dump()

        assert isinstance(dumped, dict)
        assert "model_id" in dumped
        assert "audit_timestamp" in dumped
        assert "auditor_model" in dumped
        assert "summary" in dumped
        assert "field_audits" in dumped

        # Must be JSON-serialisable
        json_str = json.dumps(dumped)
        assert isinstance(json_str, str)
        assert "org/model-name" in json_str


class TestPromptContent:
    def test_build_audit_user_prompt(self):
        """build_audit_user_prompt embeds model card text and question IDs in output."""
        model_card = "This is a sample model card for TestCorp/MyModel."
        questions = [
            {"id": "legal_name", "question": "What is the legal name?"},
            {"id": "model_name", "question": "What is the model name?"},
        ]
        prompt = build_audit_user_prompt(model_card, questions)

        assert model_card in prompt
        assert "legal_name" in prompt
        assert "model_name" in prompt

    def test_system_prompt_contains_rubric(self):
        """AUDIT_SYSTEM_PROMPT must reference all 5 score definitions and the skeptical auditor framing."""
        # Check all score definitions present
        for score_def in ("1 =", "1i =", "2 =", "3 =", "4 ="):
            assert score_def in AUDIT_SYSTEM_PROMPT, (
                f"Expected '{score_def}' in AUDIT_SYSTEM_PROMPT"
            )
        # Check skeptical framing
        assert "skeptical" in AUDIT_SYSTEM_PROMPT.lower()


class TestScoreDistribution:
    def test_score_distribution_with_counter(self):
        """collections.Counter correctly tallies a known score distribution."""
        scores = ["1", "1", "1i", "2", "4"]
        audits = [make_field_audit(question_id=f"q{i}", score=s) for i, s in enumerate(scores)]

        counts = collections.Counter(fa.score for fa in audits)
        assert counts["1"] == 2
        assert counts["1i"] == 1
        assert counts["2"] == 1
        assert counts["4"] == 1
        assert counts.get("3", 0) == 0
