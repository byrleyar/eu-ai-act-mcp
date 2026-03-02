import pytest
from pathlib import Path
from batch_processor import sanitize_model_id

def test_sanitize_model_id():
    assert sanitize_model_id("org/model") == "org__model"
    assert sanitize_model_id("simple-model") == "simple-model"
    assert sanitize_model_id("org/model/sub") == "org__model__sub"

def test_batch_directory_structure(tmp_path):
    # This is a bit more complex to test without running the whole app
    # but we can test the logic if we extract it.
    pass
