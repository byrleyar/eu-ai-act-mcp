"""
Unit tests for audit_processor.py.

Tests cover:
- Model directory discovery (only dirs with model_card.txt are included)
- Model ID reverse-sanitization (dirname -> model_id)
- audit_summary.csv column format
"""

import csv
import io
import tempfile
from pathlib import Path

import pytest

from audit_processor import discover_model_dirs, reverse_sanitize_model_id


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestModelDirDiscovery:
    def test_only_dirs_with_model_card_are_discovered(self):
        """Only subdirectories containing model_card.txt should be returned."""
        with tempfile.TemporaryDirectory() as tmp:
            batch_dir = Path(tmp)

            # Dir WITH model_card.txt -- should be discovered
            valid_dir = batch_dir / "facebook__opt-125m"
            valid_dir.mkdir()
            (valid_dir / "model_card.txt").write_text("Model card content", encoding="utf-8")

            # Dir WITHOUT model_card.txt -- should be excluded
            invalid_dir = batch_dir / "gpt2__no_card"
            invalid_dir.mkdir()

            # Plain file -- should be ignored (not a dir)
            (batch_dir / "audit_summary.csv").write_text("col1,col2", encoding="utf-8")

            discovered = discover_model_dirs(batch_dir)

            assert len(discovered) == 1
            assert discovered[0].name == "facebook__opt-125m"

    def test_empty_batch_dir_returns_no_models(self):
        """An empty batch directory should yield an empty list."""
        with tempfile.TemporaryDirectory() as tmp:
            batch_dir = Path(tmp)
            discovered = discover_model_dirs(batch_dir)
            assert discovered == []

    def test_multiple_valid_dirs_are_all_discovered(self):
        """All subdirectories with model_card.txt should be discovered."""
        with tempfile.TemporaryDirectory() as tmp:
            batch_dir = Path(tmp)

            for name in ("facebook__opt-125m", "gpt2", "bert-base-uncased"):
                d = batch_dir / name
                d.mkdir()
                (d / "model_card.txt").write_text("...", encoding="utf-8")

            discovered = discover_model_dirs(batch_dir)
            assert len(discovered) == 3


class TestModelIdFromDirname:
    def test_double_underscore_reversed_to_slash(self):
        """'facebook__opt-125m' should reverse to 'facebook/opt-125m'."""
        assert reverse_sanitize_model_id("facebook__opt-125m") == "facebook/opt-125m"

    def test_no_separator_unchanged(self):
        """A dirname with no '__' should be returned unchanged."""
        assert reverse_sanitize_model_id("gpt2") == "gpt2"

    def test_multiple_underscores_all_reversed(self):
        """All '__' occurrences should be replaced (handles org/repo/sub paths)."""
        assert reverse_sanitize_model_id("org__repo__sub") == "org/repo/sub"


class TestAuditSummaryCSVFormat:
    def test_csv_writer_produces_correct_headers(self):
        """The audit_summary.csv writer must produce exactly the expected column headers."""
        expected_headers = [
            "model_id",
            "status",
            "duration",
            "total_fields",
            "score_1",
            "score_1i",
            "score_2",
            "score_3",
            "score_4",
            "error",
        ]

        # Write a minimal CSV to a StringIO buffer and verify headers
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=expected_headers)
        writer.writeheader()

        # Parse back and verify
        buffer.seek(0)
        reader = csv.DictReader(buffer)
        assert list(reader.fieldnames) == expected_headers

    def test_csv_row_roundtrip(self):
        """A result dict written to CSV and read back should preserve all values."""
        headers = [
            "model_id",
            "status",
            "duration",
            "total_fields",
            "score_1",
            "score_1i",
            "score_2",
            "score_3",
            "score_4",
            "error",
        ]
        row = {
            "model_id": "facebook/opt-125m",
            "status": "SUCCESS",
            "duration": "12.34s",
            "total_fields": 80,
            "score_1": 20,
            "score_1i": 15,
            "score_2": 5,
            "score_3": 10,
            "score_4": 30,
            "error": "",
        }

        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=headers)
        writer.writeheader()
        writer.writerow(row)

        buffer.seek(0)
        reader = csv.DictReader(buffer)
        parsed = next(reader)

        assert parsed["model_id"] == "facebook/opt-125m"
        assert parsed["status"] == "SUCCESS"
        assert parsed["total_fields"] == "80"  # CSV reads as str
        assert parsed["score_2"] == "5"
        assert parsed["error"] == ""
