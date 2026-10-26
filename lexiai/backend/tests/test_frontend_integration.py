import pytest
import uuid
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.analysis import LegalAnalysisResult, ClauseSchema

client = TestClient(app)

def mock_generate_embeddings(texts, *args, **kwargs):
    return [[0.1] * 768 for _ in texts]

# 15. Existing frontend API integration
def test_frontend_full_integration_flow():
    # 1. User Signup & Login
    unique_email = f"frontend_user_{uuid.uuid4().hex[:6]}@example.com"
    signup_res = client.post(
        "/api/v1/auth/signup",
        json={"email": unique_email, "password": "securepassword123", "full_name": "Frontend Legal User"}
    )
    assert signup_res.status_code == 200

    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": unique_email, "password": "securepassword123"}
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Upload Document (as done in src/app/(app)/upload/page.tsx)
    contract_text = """
    EMPLOYMENT AGREEMENT
    This Agreement is entered into between Acme Tech Inc. and Jane Doe.
    1. Compensation: Employee shall receive an annual base salary of $150,000 payable semi-monthly.
    2. Termination: Either party may terminate with two (2) weeks prior written notice.
    3. Confidentiality: Employee shall protect proprietary trade secrets during and after employment.
    4. Governing Law: State of California.
    """
    upload_res = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        files={"file": ("employment_agreement.txt", contract_text.encode("utf-8"), "text/plain")}
    )
    assert upload_res.status_code == 200
    doc_data = upload_res.json()
    assert "id" in doc_data
    assert doc_data["filename"] == "employment_agreement.txt"
    doc_id = doc_data["id"]

    # 3. Poll Job Status (as done in src/app/(app)/upload/page.tsx)
    job_res = client.get(f"/api/v1/documents/jobs/{doc_id}", headers=headers)
    assert job_res.status_code == 200
    assert job_res.json()["document_id"] == doc_id

    # 4. Fetch Documents List (as done in src/app/(app)/documents/page.tsx and analysis dropdown)
    docs_res = client.get("/api/v1/documents", headers=headers)
    assert docs_res.status_code == 200
    docs_list = docs_res.json()
    assert any(d["id"] == doc_id for d in docs_list)

    # 5. Trigger Analysis (as done in src/app/(app)/analysis/page.tsx)
    mock_analysis = LegalAnalysisResult(
        executive_summary="Employment agreement between Acme Tech Inc. and Jane Doe.",
        important_points=["Two weeks notice required for termination", "Strict trade secret protections"],
        parties=["Acme Tech Inc.", "Jane Doe"],
        organizations=["Acme Tech Inc."],
        dates=["Notice period: 2 weeks"],
        payment_terms=["Annual base salary of $150,000 payable semi-monthly"],
        termination_conditions=["2 weeks written notice"],
        confidentiality=["Perpetual trade secret confidentiality"],
        jurisdiction=["State of California"],
        obligations=["Perform designated duties", "Maintain proprietary secrets"],
        clauses=[
            ClauseSchema(clause_type="Termination", title="Termination for Notice", text="2 weeks notice", source_page=1),
            ClauseSchema(clause_type="Compensation", title="Base Salary", text="$150,000 per year", source_page=1)
        ],
        risk_score=90.0
    )

    with patch("app.ai.legal_analysis.analyze_legal_text_structured", return_value=mock_analysis):
        analyze_res = client.post(f"/api/v1/documents/{doc_id}/analyze", headers=headers)
        assert analyze_res.status_code == 200
        an_data = analyze_res.json()
        assert an_data["document_id"] == doc_id
        assert an_data["summary"] == mock_analysis.executive_summary
        assert len(an_data["clauses"]) == 2
        assert an_data["risk_score"] == 90.0

    # 6. Fetch Analysis (as done in src/app/(app)/analysis/page.tsx)
    get_an_res = client.get(f"/api/v1/documents/{doc_id}/analysis", headers=headers)
    assert get_an_res.status_code == 200
    assert get_an_res.json()["summary"] == mock_analysis.executive_summary

    # 7. Ask Page Chat Query (as done in src/app/(app)/ask/page.tsx)
    mock_answer = "Under Section 1, the employee's compensation is an annual base salary of $150,000 paid semi-monthly."
    with patch("app.ai.rag_service.generate_embeddings", side_effect=mock_generate_embeddings), \
         patch("app.ai.rag_service.generate_grounded_answer", return_value=mock_answer):

        chat_res = client.post(
            "/api/v1/chat/query",
            headers=headers,
            json={
                "question": "What is the employee's salary?",
                "document_id": doc_id
            }
        )
        assert chat_res.status_code == 200
        chat_data = chat_res.json()
        assert "salary of $150,000" in chat_data["answer"]
        assert len(chat_data["sources"]) > 0
        assert chat_data["sources"][0]["document_id"] == doc_id
        assert "session_id" in chat_data
