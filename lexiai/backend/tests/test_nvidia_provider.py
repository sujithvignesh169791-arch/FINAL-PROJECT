import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.analysis import LegalAnalysisResult, ClauseSchema
from app.ai.nvidia_provider import (
    get_nvidia_client,
    analyze_legal_text_structured,
    analyze_chunk_structured,
    combine_chunk_analyses_structured,
    generate_grounded_answer,
    generate_embeddings,
    _extract_and_validate_json,
    NvidiaConfigurationError,
    NvidiaAPIError
)
from tests.test_auth import test_login

client = TestClient(app)

def test_missing_nvidia_api_key():
    with patch("app.ai.nvidia_provider.settings.NVIDIA_API_KEY", ""):
        with patch.dict("os.environ", {"NVIDIA_API_KEY": ""}):
            with pytest.raises(NvidiaConfigurationError) as exc_info:
                get_nvidia_client()
            assert "NVIDIA_API_KEY is not configured" in str(exc_info.value)

def test_get_nvidia_client_configured():
    with patch("app.ai.nvidia_provider.settings.NVIDIA_API_KEY", "nvapi-test-key-123"):
        cli = get_nvidia_client()
        assert cli.api_key == "nvapi-test-key-123"
        assert "integrate.api.nvidia.com" in str(cli.base_url)

def test_extract_and_validate_json_pure():
    sample_json = {
        "executive_summary": "Test Summary Agreement",
        "parties": ["Party Alpha", "Party Beta"],
        "dates": ["2026-10-25"],
        "payment_terms": ["Net 30"],
        "clauses": [
            {
                "clause_type": "Payment",
                "title": "Payment Terms",
                "text": "Client pays within 30 days.",
                "source_page": 1
            }
        ],
        "risk_score": 88.0
    }
    result = _extract_and_validate_json(json.dumps(sample_json))
    assert isinstance(result, LegalAnalysisResult)
    assert result.executive_summary == "Test Summary Agreement"
    assert len(result.parties) == 2
    assert result.clauses[0].clause_type == "Payment"
    assert result.risk_score == 88.0

def test_extract_and_validate_json_with_code_fences():
    raw_markdown = """```json
    {
        "executive_summary": "Extracted via markdown fence",
        "parties": ["Party One"],
        "important_points": ["First covenant"]
    }
    ```"""
    result = _extract_and_validate_json(raw_markdown)
    assert result.executive_summary == "Extracted via markdown fence"
    assert result.parties == ["Party One"]
    assert result.important_points == ["First covenant"]

def test_extract_and_validate_json_malformed():
    with pytest.raises(NvidiaAPIError) as exc_info:
        _extract_and_validate_json("not valid json at all")
    assert "Malformed JSON" in str(exc_info.value)

def test_analyze_legal_text_structured_mocked():
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps({
        "executive_summary": "NVIDIA NIM Processed Contract",
        "parties": ["LexiCorp", "Client Co"],
        "clauses": [
            {"clause_type": "Liability", "title": "Cap", "text": "Capped at $1M"}
        ]
    })
    mock_response = MagicMock(choices=[mock_choice])

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    with patch("app.ai.nvidia_provider.get_nvidia_client", return_value=mock_client):
        result = analyze_legal_text_structured("Test legal text")
        assert result.executive_summary == "NVIDIA NIM Processed Contract"
        assert "LexiCorp" in result.parties
        assert len(result.clauses) == 1

def test_analyze_chunk_structured_mocked():
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps({
        "executive_summary": "Chunk 1 summary",
        "parties": ["Acme Corp"]
    })
    mock_response = MagicMock(choices=[mock_choice])

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    with patch("app.ai.nvidia_provider.get_nvidia_client", return_value=mock_client):
        result = analyze_chunk_structured(chunk_text="Chunk text", chunk_index=1, total_chunks=3)
        assert result.executive_summary == "Chunk 1 summary"
        assert result.parties == ["Acme Corp"]

def test_combine_chunk_analyses_mocked():
    chunk1 = LegalAnalysisResult(
        executive_summary="Part 1 summary",
        parties=["Party A"]
    )
    chunk2 = LegalAnalysisResult(
        executive_summary="Part 2 summary",
        parties=["Party B"]
    )

    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps({
        "executive_summary": "Consolidated full agreement summary",
        "parties": ["Party A", "Party B"]
    })
    mock_response = MagicMock(choices=[mock_choice])

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    with patch("app.ai.nvidia_provider.get_nvidia_client", return_value=mock_client):
        result = combine_chunk_analyses_structured([chunk1, chunk2])
        assert result.executive_summary == "Consolidated full agreement summary"
        assert result.parties == ["Party A", "Party B"]

def test_generate_grounded_answer_mocked():
    mock_choice = MagicMock()
    mock_choice.message.content = "According to Section 4, payment is due in 30 days."
    mock_response = MagicMock(choices=[mock_choice])

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    with patch("app.ai.nvidia_provider.get_nvidia_client", return_value=mock_client):
        answer = generate_grounded_answer(
            question="When is payment due?",
            context="[Source: Doc, Page 1] Section 4: Payment due in 30 days."
        )
        assert "Section 4" in answer
        assert "30 days" in answer

def test_generate_embeddings_mocked():
    mock_data = [MagicMock(embedding=[0.05] * 2048), MagicMock(embedding=[0.1] * 2048)]
    mock_response = MagicMock(data=mock_data)

    mock_client = MagicMock()
    mock_client.embeddings.create.return_value = mock_response

    with patch("app.ai.nvidia_provider.get_nvidia_client", return_value=mock_client):
        embeddings = generate_embeddings(["Clause 1", "Clause 2"])
        assert len(embeddings) == 2
        assert len(embeddings[0]) == 2048
        assert embeddings[0][0] == 0.05

def test_extract_and_validate_json_missing_comma_repair():
    # Malformed JSON with missing comma between list items and missing comma after object field
    malformed_raw = """
    {
        "executive_summary": "Extracted judgment with syntax defect"
        "parties": ["Petitioner" "Respondent"],
        "important_points": [
            "Point 1"
            "Point 2"
        ],
        "clauses": [
            {
                "clause_type": "Precedent",
                "title": "Ruling",
                "text": "The High Court dismissed the application."
            }
        ],
        "risk_score": 82.0,
    }
    """
    result = _extract_and_validate_json(malformed_raw)
    assert isinstance(result, LegalAnalysisResult)
    assert result.executive_summary == "Extracted judgment with syntax defect"
    assert len(result.parties) == 2
    assert len(result.important_points) == 2
    assert len(result.clauses) == 1
    assert result.risk_score == 82.0


