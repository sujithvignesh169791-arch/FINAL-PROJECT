import os
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.corpus import PublicCorpusDocument
from app.services.dataset_ingestion import (
    clean_legal_text,
    resolve_cuad_path,
    resolve_cjpe_path,
    ingest_cuad_contracts,
    ingest_supreme_court_judgments,
    ingest_initial_corpus_sample
)
from app.ai.rag_service import (
    get_user_collection_name,
    get_public_corpus_collection_name,
    get_document_collection,
    get_public_corpus_collection,
    retrieve_public_corpus_chunks
)
from tests.test_auth import test_login

client = TestClient(app)

def test_clean_legal_text():
    raw = "‘Smart quotes’ and “double quotes” – dash — em-dash\x00\x08\n\n\n\nMultiple lines."
    cleaned = clean_legal_text(raw)
    assert "'" in cleaned
    assert '"' in cleaned
    assert "\x00" not in cleaned
    assert "\n\n\n\n" not in cleaned
    assert "Multiple lines." in cleaned

def test_path_resolution():
    cuad_path = resolve_cuad_path(settings.DATASET_ROOT_PATH)
    assert cuad_path is not None, f"CUAD directory not found at {settings.DATASET_ROOT_PATH}"
    assert (cuad_path / "master_clauses.csv").exists()

    cjpe_path = resolve_cjpe_path(settings.DATASET_ROOT_PATH)
    assert cjpe_path is not None, f"CJPE file not found at {settings.DATASET_ROOT_PATH}"
    assert cjpe_path.exists()

def test_dry_run_ingestion():
    db = SessionLocal()
    try:
        res = ingest_initial_corpus_sample(
            db=db,
            contracts_limit=5,
            judgments_limit=5,
            dry_run=True
        )
        assert res["status"] == "dry_run"
        assert res["contracts"]["processed_count"] == 5
        assert res["judgments"]["processed_count"] == 5
        assert res["total_ingested"] == 10

        # Verify contracts metadata
        c_items = res["contracts"]["items"]
        assert len(c_items) == 5
        for item in c_items:
            assert item["corpus_type"] == "CUAD_CONTRACT"
            assert len(item["title"]) > 0
            assert item["filename"].endswith(".txt")
            assert len(item["parties"]) >= 1
            assert item["text_length"] > 1000

        # Verify judgments metadata
        j_items = res["judgments"]["items"]
        assert len(j_items) == 5
        for item in j_items:
            assert item["corpus_type"] == "INDIAN_SUPREME_COURT"
            assert "Supreme Court of India" in item["court"]
            assert "INSC" in item["citation"]
            assert item["verdict"] in ("Accepted", "Rejected")
            assert item["text_length"] > 1000
    finally:
        db.close()

def test_duplicate_skipping_safety():
    db = SessionLocal()
    try:
        # Re-running live sample ingestion should skip all existing documents safely
        res = ingest_initial_corpus_sample(
            db=db,
            contracts_limit=5,
            judgments_limit=5,
            dry_run=False
        )
        # All 10 already exist in database from prior ingestion
        assert res["total_skipped"] == 10
        assert res["total_ingested"] == 0
    finally:
        db.close()

def test_public_corpus_separation_from_user_documents():
    # User document collection name vs Public corpus collection name
    user_coll_nvidia = get_user_collection_name(2048)
    public_coll_nvidia = get_public_corpus_collection_name(2048)
    assert user_coll_nvidia != public_coll_nvidia
    assert user_coll_nvidia.startswith("lexiai_documents_")
    assert public_coll_nvidia.startswith("lexiai_public_corpus_")

    # Dimensions
    user_coll_768 = get_user_collection_name(768)
    public_coll_768 = get_public_corpus_collection_name(768)
    assert user_coll_768 != user_coll_nvidia
    assert public_coll_768 != public_coll_nvidia

def test_case_recommendations_grounded_in_public_corpus():
    token = test_login()
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/cases/recommendations", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "precedents" in data
    assert len(data["precedents"]) >= 3

    # Every precedent must have real metadata
    for p in data["precedents"]:
        assert len(p["name"]) > 0
        assert len(p["court"]) > 0
        assert len(p["year"]) > 0
        assert len(p["filename"]) > 0
        assert len(p["desc"]) > 0
        # No hallucinated empty strings
        assert "None" not in p["name"]

def test_public_corpus_listing_api():
    token = test_login()
    headers = {"Authorization": f"Bearer {token}"}

    # Query all
    res_all = client.get("/api/v1/cases/public-corpus?limit=20", headers=headers)
    assert res_all.status_code == 200
    docs = res_all.json()
    assert len(docs) >= 10

    # Query CUAD only
    res_cuad = client.get("/api/v1/cases/public-corpus?corpus_type=CUAD_CONTRACT", headers=headers)
    assert res_cuad.status_code == 200
    cuad_docs = res_cuad.json()
    assert len(cuad_docs) >= 5
    assert all(d["corpus_type"] == "CUAD_CONTRACT" for d in cuad_docs)

    # Query Supreme Court only
    res_sci = client.get("/api/v1/cases/public-corpus?corpus_type=INDIAN_SUPREME_COURT", headers=headers)
    assert res_sci.status_code == 200
    sci_docs = res_sci.json()
    assert len(sci_docs) >= 5
    assert all(d["corpus_type"] == "INDIAN_SUPREME_COURT" for d in sci_docs)
    assert all("Supreme Court of India" in d["court_or_jurisdiction"] for d in sci_docs)

