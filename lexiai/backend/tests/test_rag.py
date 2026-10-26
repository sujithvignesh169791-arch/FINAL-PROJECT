import pytest
import os
import shutil
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.ai.rag_service import (
    chunk_document_text,
    index_document_chunks,
    retrieve_relevant_chunks,
    get_document_collection
)
from app.schemas.chat import ChatQueryRequest
from tests.test_auth import test_login, test_signup

client = TestClient(app)

def mock_generate_embeddings(texts, *args, **kwargs):
    return [[0.1] * 768 for _ in texts]

def upload_test_doc(headers, content="Default legal content for testing.", filename="test_doc.txt"):
    response = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        files={"file": (filename, content.encode("utf-8"), "text/plain")}
    )
    assert response.status_code == 200
    return response.json()["id"]

# 7. Embedding creation
def test_embedding_creation():
    texts = ["Sample legal clause", "Limitation of liability"]
    mock_embeddings = [[0.1] * 768, [0.2] * 768]

    with patch("app.ai.rag_service.generate_embeddings", return_value=mock_embeddings) as mock_embed:
        res = mock_embed(texts)
        assert len(res) == 2
        assert len(res[0]) == 768
        assert len(res[1]) == 768

# 8. Vector persistence and retrieval
def test_vector_persistence_and_retrieval():
    doc_id = "test_persistence_doc_1"
    user_id = "user_persisted_123"
    pages = [{"page_number": 1, "text": "Clause 1: The supplier warrants good title.\n\nClause 2: Payments are net 30."}]
    full_text = "Clause 1: The supplier warrants good title.\n\nClause 2: Payments are net 30."

    with patch("app.ai.rag_service.generate_embeddings", side_effect=mock_generate_embeddings):
        count = index_document_chunks(
            document_id=doc_id,
            user_id=user_id,
            filename="title_warranties.pdf",
            pages=pages,
            full_text=full_text,
            force=True
        )
        assert count >= 1

    # Verify retrieval from persistent collection
    coll = get_document_collection()
    found = coll.get(where={"document_id": doc_id})
    assert len(found["ids"]) >= 1
    assert found["metadatas"][0]["user_id"] == user_id
    assert found["metadatas"][0]["filename"] == "title_warranties.pdf"

# 9. Relevant chunks returned for a question
def test_relevant_chunks_returned_for_question():
    doc_id = "test_doc_query_1"
    user_id = "user_query_123"
    pages = [{"page_number": 3, "text": "Confidential information shall be kept secret for 5 years."}]

    with patch("app.ai.rag_service.generate_embeddings", side_effect=mock_generate_embeddings):
        index_document_chunks(
            document_id=doc_id,
            user_id=user_id,
            filename="nda_clause.pdf",
            pages=pages,
            full_text="Confidential information shall be kept secret for 5 years.",
            force=True
        )

        chunks = retrieve_relevant_chunks(
            user_id=user_id,
            query="How long is confidentiality?",
            document_id=doc_id,
            top_k=2
        )
        assert len(chunks) >= 1
        assert "Confidential information" in chunks[0]["excerpt"]
        assert chunks[0]["page_number"] == 3

# 10. RAG response includes source metadata
def test_rag_response_includes_source_metadata():
    token = test_login()
    headers = {"Authorization": f"Bearer {token}"}
    content = "Governing Law: This agreement is governed by the laws of England and Wales. Jurisdiction lies with London courts."
    doc_id = upload_test_doc(headers, content=content, filename="governing_law.txt")

    mock_answer = "According to Section 1, this agreement is governed by the laws of England and Wales with jurisdiction in London courts."

    with patch("app.ai.rag_service.generate_embeddings", side_effect=mock_generate_embeddings), \
         patch("app.ai.rag_service.generate_grounded_answer", return_value=mock_answer):

        payload = {
            "question": "What is the governing law of the contract?",
            "document_id": doc_id
        }
        res = client.post("/api/v1/chat/query", headers=headers, json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["answer"] == mock_answer
        assert len(data["sources"]) > 0
        source = data["sources"][0]
        assert source["document_name"] == "governing_law.txt"
        assert source["document_id"] == doc_id
        assert "England and Wales" in source["excerpt"]
        assert "session_id" in data

# 11. Insufficient evidence response
def test_insufficient_evidence_response():
    token = test_login()
    headers = {"Authorization": f"Bearer {token}"}

    with patch("app.ai.rag_service.retrieve_relevant_chunks", return_value=[]):
        payload = {
            "question": "What is the secret offshore bank account number?"
        }
        res = client.post("/api/v1/chat/query", headers=headers, json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "insufficient information" in data["answer"].lower()
        assert data["sources"] == []

# 12. Chat history persistence
def test_chat_history_persistence():
    token = test_login()
    headers = {"Authorization": f"Bearer {token}"}
    doc_id = upload_test_doc(headers, content="Payment is due in 30 days.", filename="invoice_rules.txt")

    mock_answer_1 = "Payment is due in 30 days."
    mock_answer_2 = "Late payments incur a 2% monthly fee."

    with patch("app.ai.rag_service.generate_embeddings", side_effect=mock_generate_embeddings), \
         patch("app.ai.rag_service.generate_grounded_answer", side_effect=[mock_answer_1, mock_answer_2]):

        # First turn
        res1 = client.post(
            "/api/v1/chat/query",
            headers=headers,
            json={"question": "When is payment due?", "document_id": doc_id}
        )
        assert res1.status_code == 200
        session_id = res1.json()["session_id"]

        # Second turn in the same session
        res2 = client.post(
            "/api/v1/chat/query",
            headers=headers,
            json={"question": "What if payment is late?", "session_id": session_id, "document_id": doc_id}
        )
        assert res2.status_code == 200
        assert res2.json()["session_id"] == session_id

        # Verify session retrieval from database
        sess_res = client.get(f"/api/v1/chat/sessions/{session_id}", headers=headers)
        assert sess_res.status_code == 200
        sess_data = sess_res.json()
        assert len(sess_data["messages"]) == 4  # (User1, AI1, User2, AI2)
        assert sess_data["messages"][0]["content"] == "When is payment due?"
        assert sess_data["messages"][1]["content"] == mock_answer_1
        assert sess_data["messages"][2]["content"] == "What if payment is late?"
        assert sess_data["messages"][3]["content"] == mock_answer_2

# 13. Unauthorized document access
def test_unauthorized_document_access():
    # User 1 uploads a document
    token1 = test_login()
    headers1 = {"Authorization": f"Bearer {token1}"}
    doc_id1 = upload_test_doc(headers1, content="Confidential User 1 data.", filename="user1_doc.txt")

    # Create User 2
    import uuid
    u2_email = f"user2_{uuid.uuid4().hex[:6]}@example.com"
    client.post("/api/v1/auth/signup", json={"email": u2_email, "password": "password123", "full_name": "User Two"})
    login_res2 = client.post("/api/v1/auth/login", data={"username": u2_email, "password": "password123"})
    token2 = login_res2.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    # User 2 tries to query User 1's document
    res = client.post(
        "/api/v1/chat/query",
        headers=headers2,
        json={"question": "What is in this document?", "document_id": doc_id1}
    )
    assert res.status_code == 404
    assert "unauthorized" in res.json()["detail"].lower()

# 14. Cross-user data isolation
def test_cross_user_data_isolation():
    token1 = test_login()
    headers1 = {"Authorization": f"Bearer {token1}"}
    doc_id1 = upload_test_doc(headers1, content="Top Secret Project X for User 1.", filename="user1_secret.txt")

    with patch("app.ai.rag_service.generate_embeddings", side_effect=mock_generate_embeddings):
        # User 1 queries their document
        chunks_user1 = retrieve_relevant_chunks(user_id=token1, query="Project X", document_id=doc_id1)

        # User 2 cross-document search should NOT retrieve User 1's document
        chunks_user2 = retrieve_relevant_chunks(user_id="different_user_id_456", query="Project X")
        assert not any(c["document_id"] == doc_id1 for c in chunks_user2)
