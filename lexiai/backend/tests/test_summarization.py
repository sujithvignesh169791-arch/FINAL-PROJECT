import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.analysis import LegalAnalysisResult, ClauseSchema
from app.ai.gemini_provider import GeminiConfigurationError, GeminiAPIError
from tests.test_auth import test_login

client = TestClient(app)

def create_sample_legal_result():
    return LegalAnalysisResult(
        executive_summary="This is a binding Master Services Agreement between LexiCorp and Client Ltd.",
        important_points=[
            "Payment is due within 30 days of monthly invoice.",
            "Independent audit rights granted annually."
        ],
        parties=["LexiCorp LLC", "Client Ltd."],
        organizations=["LexiCorp LLC", "Client Ltd."],
        dates=["Effective Date: January 1, 2026", "Termination Date: December 31, 2027"],
        legal_acts=["Commercial Transactions Act 2020"],
        legal_sections=["Section 12.4 (Indemnity)", "Section 8.1 (Payment)"],
        payment_terms=["Net 30 payment terms via electronic wire"],
        penalties=["1.5% late fee per month on overdue invoices"],
        termination_conditions=["30 days written notice for convenience"],
        liability_and_indemnity=["Total aggregate liability capped at 12 months fees"],
        confidentiality=["Obligations survive 5 years following termination"],
        dispute_resolution=["Binding arbitration under AAA rules in New York"],
        jurisdiction=["State of New York, USA"],
        obligations=["Deliver monthly service reports", "Maintain $2M cyber liability insurance"],
        clauses=[
            ClauseSchema(
                clause_type="Limitation of Liability",
                title="Liability Limitation",
                text="Neither party shall be liable for consequential or indirect damages.",
                source_page=1
            ),
            ClauseSchema(
                clause_type="Confidentiality",
                title="Confidential Information",
                text="Each party agrees to maintain confidentiality of proprietary data.",
                source_page=1
            )
        ],
        risk_score=85.0
    )

def upload_test_doc(headers, content="Standard legal contract content for testing.", filename="contract.txt"):
    response = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        files={"file": (filename, content.encode("utf-8"), "text/plain")}
    )
    assert response.status_code == 200
    doc_id = response.json()["id"]
    return doc_id

# 1. Successful summarization
def test_successful_summarization():
    token = test_login()
    headers = {"Authorization": f"Bearer {token}"}
    doc_id = upload_test_doc(headers)

    mock_result = create_sample_legal_result()
    with patch("app.ai.legal_analysis.analyze_legal_text_structured", return_value=mock_result):
        res = client.post(f"/api/v1/documents/{doc_id}/analyze", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["document_id"] == doc_id
        assert "Master Services Agreement" in data["summary"]
        assert data["risk_score"] == 85.0
        assert len(data["clauses"]) == 2
        assert data["clauses"][0]["clause_type"] == "Limitation of Liability"
        assert "parties" in data["extracted_entities"]
        assert "LexiCorp LLC" in data["extracted_entities"]["parties"]

# 2. Invalid API configuration
def test_invalid_api_configuration():
    token = test_login()
    headers = {"Authorization": f"Bearer {token}"}
    doc_id = upload_test_doc(headers)

    with patch("app.ai.legal_analysis.analyze_legal_text_structured", side_effect=GeminiConfigurationError("GEMINI_API_KEY is not configured")):
        res = client.post(f"/api/v1/documents/{doc_id}/analyze", headers=headers)
        assert res.status_code == 500
        assert "Gemini configuration error" in res.json()["detail"]

# 3. Gemini API failure
def test_gemini_api_failure():
    token = test_login()
    headers = {"Authorization": f"Bearer {token}"}
    doc_id = upload_test_doc(headers)

    with patch("app.ai.legal_analysis.analyze_legal_text_structured", side_effect=GeminiAPIError("Rate limit exceeded")):
        res = client.post(f"/api/v1/documents/{doc_id}/analyze", headers=headers)
        assert res.status_code == 502
        assert "Gemini API failure" in res.json()["detail"]

# 4. Long-document chunking
def test_long_document_chunking():
    token = test_login()
    headers = {"Authorization": f"Bearer {token}"}
    # Create long text exceeding 12,000 characters
    long_text = ("This is a comprehensive multi-clause legal agreement.\n\nSection 1: Terms.\n" * 300)
    doc_id = upload_test_doc(headers, content=long_text, filename="long_agreement.txt")

    mock_chunk_result = create_sample_legal_result()
    mock_combined_result = create_sample_legal_result()
    mock_combined_result.executive_summary = "Consolidated summary of long document."

    with patch("app.ai.legal_analysis.analyze_chunk_structured", return_value=mock_chunk_result) as mock_chunk, \
         patch("app.ai.legal_analysis.combine_chunk_analyses_structured", return_value=mock_combined_result) as mock_combine:
        
        res = client.post(f"/api/v1/documents/{doc_id}/analyze", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["summary"] == "Consolidated summary of long document."
        assert mock_chunk.call_count >= 1
        assert mock_combine.call_count == 1

# 5. Structured response validation
def test_structured_response_validation():
    # Empty/missing fields must default to empty lists or strings, not nulls
    empty_result = LegalAnalysisResult()
    assert empty_result.executive_summary == ""
    assert empty_result.parties == []
    assert empty_result.clauses == []
    assert empty_result.risk_score == 75.0

    # Ensure model validation parses dictionary input correctly
    raw_dict = {
        "executive_summary": "Test Summary",
        "parties": ["Party 1"],
        "clauses": [
            {"clause_type": "Payment", "title": "Invoicing", "text": "Net 30 days", "source_page": 2}
        ]
    }
    validated = LegalAnalysisResult.model_validate(raw_dict)
    assert validated.executive_summary == "Test Summary"
    assert len(validated.clauses) == 1
    assert validated.clauses[0].source_page == 2

# 6. Analysis persistence
def test_analysis_persistence():
    token = test_login()
    headers = {"Authorization": f"Bearer {token}"}
    doc_id = upload_test_doc(headers)

    mock_result = create_sample_legal_result()
    with patch("app.ai.legal_analysis.analyze_legal_text_structured", return_value=mock_result):
        client.post(f"/api/v1/documents/{doc_id}/analyze", headers=headers)

    # Calling GET /analysis should retrieve the persisted database record without re-analyzing
    with patch("app.ai.legal_analysis.analyze_legal_text_structured") as mock_should_not_call:
        res = client.get(f"/api/v1/documents/{doc_id}/analysis", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["document_id"] == doc_id
        assert "Master Services Agreement" in data["summary"]
        assert mock_should_not_call.call_count == 0
