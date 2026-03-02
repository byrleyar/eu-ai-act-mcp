import pytest
from pathlib import Path
from batch_processor import sanitize_model_id

def test_sanitize_model_id():
    assert sanitize_model_id("org/model") == "org__model"
    assert sanitize_model_id("simple-model") == "simple-model"
    assert sanitize_model_id("org/model/sub") == "org__model__sub"

def test_batch_directory_structure(tmp_path):
    output_dir = tmp_path / "batches"
    batch_root = output_dir / "batch_2026-03-02_1200"
    batch_root.mkdir(parents=True, exist_ok=True)

    safe_name = sanitize_model_id("org/model")
    model_dir = batch_root / safe_name
    model_dir.mkdir(parents=True, exist_ok=True)

    assert batch_root.exists()
    assert model_dir.exists()
    assert model_dir.name == "org__model"
    assert model_dir.parent == batch_root

    # Verify exist_ok=True does not raise on re-creation
    model_dir.mkdir(parents=True, exist_ok=True)
