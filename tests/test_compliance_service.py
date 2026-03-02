import pytest
import os
import json
from compliance_service import ComplianceService, ProcessingContext

def test_is_safe_url():
    service = ComplianceService()
    assert service.is_safe_url("https://huggingface.co") == True
    assert service.is_safe_url("http://google.com") == True
    assert service.is_safe_url("https://localhost") == False
    assert service.is_safe_url("https://127.0.0.1") == False
    assert service.is_safe_url("https://192.168.1.1") == False

def test_transform_arxiv_url():
    service = ComplianceService()
    assert service.transform_arxiv_url("https://arxiv.org/abs/2301.00001") == "https://arxiv.org/pdf/2301.00001.pdf"
    assert service.transform_arxiv_url("https://google.com") == "https://google.com"

def test_processing_context():
    ctx = ProcessingContext(model_id="org/model", output_path="/tmp")
    assert ctx.model_id == "org/model"
    assert len(ctx.session_id) == 8
