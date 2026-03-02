"""Unit tests for report_generator.py.

Covers:
  - SECTION_MAP completeness (80 IDs, no duplicates, 8 sections)
  - compute_metrics (normal, zero-fields, all-accurate)
  - load_audit_results (missing file, valid file)
  - ReportGenerator.discover_audited_models (discovery, key remapping)
  - ReportGenerator.write_csv (header, row count, percentage range)
"""

import csv
import json
from pathlib import Path

import pytest

from report_generator import (
    SECTION_MAP,
    CSV_FIELDNAMES,
    ReportGenerator,
    compute_metrics,
    load_audit_results,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MINIMAL_AUDIT_DATA = {
    "model_id": "test/model",
    "audit_timestamp": "2026-03-02T00:00:00Z",
    "auditor_model": "test",
    "summary": {
        "total_fields": 2,
        "score_1_count": 1,
        "score_1i_count": 0,
        "score_2_count": 1,
        "score_3_count": 0,
        "score_4_count": 0,
    },
    "field_audits": [
        {
            "question_id": "q1",
            "answer": "a",
            "score": "1",
            "score_label": "Accurate",
            "source_quote": "q",
            "source_section": "s",
            "confidence": "DIRECT",
            "reasoning": "r",
        },
        {
            "question_id": "q2",
            "answer": "b",
            "score": "2",
            "score_label": "Hallucinated",
            "source_quote": "",
            "source_section": "",
            "confidence": "NOT FOUND",
            "reasoning": "r",
        },
    ],
}


# ---------------------------------------------------------------------------
# SECTION_MAP tests
# ---------------------------------------------------------------------------


def test_section_map_covers_all_questions():
    """SECTION_MAP must cover exactly the same IDs as questions.json."""
    questions_path = Path(__file__).parent.parent / "questions.json"
    with open(questions_path, encoding="utf-8") as f:
        questions = json.load(f)
    expected_ids = {q["id"] for q in questions}
    mapped_ids = {qid for qids in SECTION_MAP.values() for qid in qids}
    assert mapped_ids == expected_ids
    assert len(mapped_ids) == 80


def test_section_map_no_duplicates():
    """No question ID should appear in more than one section."""
    all_ids_list = [qid for qids in SECTION_MAP.values() for qid in qids]
    assert len(all_ids_list) == len(set(all_ids_list))


def test_section_map_has_8_sections():
    """SECTION_MAP must have exactly 8 sections."""
    assert len(SECTION_MAP) == 8


# ---------------------------------------------------------------------------
# compute_metrics tests
# ---------------------------------------------------------------------------


def test_compute_metrics_normal():
    """Standard metric computation with mixed scores."""
    result = compute_metrics({
        "score_1": 40,
        "score_1i": 10,
        "score_2": 5,
        "score_3": 5,
        "score_4": 20,
        "total_fields": 80,
    })
    assert result["accuracy_rate"] == pytest.approx(0.625)      # (40+10)/80
    assert result["hallucination_rate"] == pytest.approx(0.0625)  # 5/80
    assert result["gap_rate"] == pytest.approx(0.0625)           # 5/80
    assert result["na_rate"] == pytest.approx(0.25)              # 20/80
    assert result["pass_rate"] == pytest.approx(0.875)           # (40+10+20)/80
    assert result["fail_rate"] == pytest.approx(0.125)           # (5+5)/80


def test_compute_metrics_zero_fields():
    """All rates should be 0.0 when total_fields is 0."""
    result = compute_metrics({
        "score_1": 0,
        "score_1i": 0,
        "score_2": 0,
        "score_3": 0,
        "score_4": 0,
        "total_fields": 0,
    })
    for rate in result.values():
        assert rate == 0.0


def test_compute_metrics_all_accurate():
    """When all 80 fields score 1, accuracy and pass rates are 1.0."""
    result = compute_metrics({
        "score_1": 80,
        "score_1i": 0,
        "score_2": 0,
        "score_3": 0,
        "score_4": 0,
        "total_fields": 80,
    })
    assert result["accuracy_rate"] == pytest.approx(1.0)
    assert result["pass_rate"] == pytest.approx(1.0)
    assert result["fail_rate"] == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# load_audit_results tests
# ---------------------------------------------------------------------------


def test_load_audit_results_missing_file(tmp_path):
    """Returns None when audit_results.json does not exist."""
    result = load_audit_results(tmp_path)
    assert result is None


def test_load_audit_results_valid(tmp_path):
    """Returns correct structure when audit_results.json exists."""
    audit_path = tmp_path / "audit_results.json"
    audit_path.write_text(json.dumps(MINIMAL_AUDIT_DATA), encoding="utf-8")

    result = load_audit_results(tmp_path)
    assert result is not None
    assert "scores_by_qid" in result
    assert len(result["scores_by_qid"]) == 2
    assert result["scores_by_qid"]["q1"] == "1"
    assert result["scores_by_qid"]["q2"] == "2"


# ---------------------------------------------------------------------------
# ReportGenerator.discover_audited_models tests
# ---------------------------------------------------------------------------


def test_discover_audited_models(tmp_path):
    """Only model dirs with audit_results.json are returned."""
    # Model 1: has audit data
    model1 = tmp_path / "model1"
    model1.mkdir()
    (model1 / "audit_results.json").write_text(
        json.dumps(MINIMAL_AUDIT_DATA), encoding="utf-8"
    )

    # Model 2: no audit data
    model2 = tmp_path / "model2"
    model2.mkdir()

    generator = ReportGenerator()
    results = generator.discover_audited_models(tmp_path)
    assert len(results) == 1


def test_discover_audited_models_metrics(tmp_path):
    """Validates score_1_count -> score_1 key remapping in discover_audited_models.

    If the remapping is absent, accuracy_rate would be 0.0 because compute_metrics
    would receive keys score_1_count (unrecognised) rather than score_1.
    """
    model_dir = tmp_path / "remap__model"
    model_dir.mkdir()
    audit_data = {
        "model_id": "test/remap-model",
        "audit_timestamp": "2026-03-02T00:00:00Z",
        "auditor_model": "test",
        "summary": {
            "total_fields": 5,
            "score_1_count": 3,
            "score_1i_count": 1,
            "score_2_count": 1,
            "score_3_count": 0,
            "score_4_count": 0,
        },
        "field_audits": [
            {
                "question_id": f"q{i}",
                "answer": "a",
                "score": "1",
                "score_label": "Accurate",
                "source_quote": "q",
                "source_section": "s",
                "confidence": "DIRECT",
                "reasoning": "r",
            }
            for i in range(5)
        ],
    }
    (model_dir / "audit_results.json").write_text(
        json.dumps(audit_data), encoding="utf-8"
    )

    generator = ReportGenerator()
    results = generator.discover_audited_models(tmp_path)
    assert len(results) == 1
    # (3 + 1) / 5 = 0.8 -- only works if remapping was applied
    assert results[0]["metrics"]["accuracy_rate"] == pytest.approx(0.8)


# ---------------------------------------------------------------------------
# ReportGenerator.write_csv tests
# ---------------------------------------------------------------------------


def test_write_csv(tmp_path):
    """write_csv writes correct headers, 2 data rows, and valid pct values."""
    models = [
        {
            "model_id": "org/model-a",
            "score_counts": {
                "score_1": 60,
                "score_1i": 10,
                "score_2": 5,
                "score_3": 5,
                "score_4": 0,
                "total_fields": 80,
            },
            "metrics": compute_metrics({
                "score_1": 60,
                "score_1i": 10,
                "score_2": 5,
                "score_3": 5,
                "score_4": 0,
                "total_fields": 80,
            }),
        },
        {
            "model_id": "org/model-b",
            "score_counts": {
                "score_1": 40,
                "score_1i": 20,
                "score_2": 10,
                "score_3": 5,
                "score_4": 5,
                "total_fields": 80,
            },
            "metrics": compute_metrics({
                "score_1": 40,
                "score_1i": 20,
                "score_2": 10,
                "score_3": 5,
                "score_4": 5,
                "total_fields": 80,
            }),
        },
    ]

    generator = ReportGenerator()
    csv_path = generator.write_csv(tmp_path, models)

    assert csv_path.exists()

    with open(csv_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == CSV_FIELDNAMES
        rows = list(reader)

    assert len(rows) == 2

    # Verify accuracy_pct is a float in 0-100 range
    for row in rows:
        acc = float(row["accuracy_pct"])
        assert 0.0 <= acc <= 100.0
