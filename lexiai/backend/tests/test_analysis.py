from fastapi.testclient import TestClient
from app.main import app
from app.db.base import Base
from app.db.session import engine
from tests.test_auth import test_login
from app.schemas.analysis import LegalAnalysisResult
from unittest.mock import patch
import pytest
import os
from app.models.document import Document
from app.models.analysis import DocumentAnalysis
from app.db.session import SessionLocal
import uuid

client = TestClient(app)

def test_document_analyze():
    token = test_login()
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Upload a file to get a valid document belonging to the test user
    with open("test.txt", "w") as f:
        f.write("This is a test contract between Party A and Party B.")
        
    with open("test.txt", "rb") as f:
        response = client.post(
            "/api/v1/documents/upload",
            headers=headers,
            files={"file": ("test.txt", f, "text/plain")}
        )
    if os.path.exists("test.txt"):
        os.remove("test.txt")
    assert response.status_code == 200
    doc_id = response.json()["id"]
    
    # Let the background task finish
    import time
    time.sleep(1) 
    
    mock_res = LegalAnalysisResult(
        executive_summary="Verified legal summary of test contract between Party A and Party B.",
        important_points=["Party A delivers services", "Party B pays remuneration"],
        parties=["Party A", "Party B"],
        risk_score=80.0
    )

    # 2. Call analyze endpoint
    with patch("app.ai.legal_analysis.analyze_legal_text_structured", return_value=mock_res):
        response_analyze = client.post(f"/api/v1/documents/{doc_id}/analyze", headers=headers)
        assert response_analyze.status_code == 200
        data = response_analyze.json()
        assert data["document_id"] == doc_id
        assert "Verified legal summary" in data["summary"]
        
        # 3. Call get analysis endpoint
        response_get = client.get(f"/api/v1/documents/{doc_id}/analysis", headers=headers)
        assert response_get.status_code == 200
        data_get = response_get.json()
        assert data_get["summary"] == data["summary"]
