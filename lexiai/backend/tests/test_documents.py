from fastapi.testclient import TestClient
from app.main import app
from app.db.base import Base
from app.db.session import engine, SessionLocal
from tests.test_auth import test_login
import pytest
import os

client = TestClient(app)

def test_document_upload_unauthorized():
    response = client.post("/api/v1/documents/upload")
    assert response.status_code == 401

def test_document_upload_txt():
    token = test_login()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a dummy txt file
    with open("test.txt", "w") as f:
        f.write("Hello World")
        
    with open("test.txt", "rb") as f:
        response = client.post(
            "/api/v1/documents/upload",
            headers=headers,
            files={"file": ("test.txt", f, "text/plain")}
        )
        
    os.remove("test.txt")
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test.txt"
    assert data["file_type"] == "txt"
    assert data["upload_status"] == "processing"
    
    # Check jobs endpoint
    doc_id = data["id"]
    job_response = client.get(f"/api/v1/documents/jobs/{doc_id}", headers=headers)
    assert job_response.status_code == 200
    
    # Give background task time to run? In TestClient, background tasks run after returning response.
    # But for async we might need to await. Actually TestClient executes background tasks synchronously before returning!
    job_response = client.get(f"/api/v1/documents/jobs/{doc_id}", headers=headers)
    assert job_response.json()["status"] in ["processing", "completed"]

def test_get_documents():
    token = test_login()
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/documents", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_document_upload_docx():
    from docx import Document as DocxDoc
    doc = DocxDoc()
    doc.add_paragraph("This is a test confidential commercial contract.")
    doc.save("test_agreement.docx")
    
    token = test_login()
    headers = {"Authorization": f"Bearer {token}"}
    try:
        with open("test_agreement.docx", "rb") as f:
            response = client.post(
                "/api/v1/documents/upload",
                headers=headers,
                files={"file": ("test_agreement.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            )
        assert response.status_code == 200
        doc_id = response.json()["id"]
        job_response = client.get(f"/api/v1/documents/jobs/{doc_id}", headers=headers)
        assert job_response.status_code == 200
        assert job_response.json()["status"] == "completed"
    finally:
        if os.path.exists("test_agreement.docx"):
            os.remove("test_agreement.docx")

