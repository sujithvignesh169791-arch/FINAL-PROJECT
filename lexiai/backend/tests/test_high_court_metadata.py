import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.high_court_service import HighCourtMetadataService, get_high_court_service

client = TestClient(app)

def test_high_court_service_direct():
    svc = get_high_court_service()
    courts = svc.get_all_high_courts()
    assert len(courts) >= 25, f"Expected at least 25 High Courts, got {len(courts)}"

    first = courts[0]
    assert "court_code" in first
    assert "court_name" in first
    assert "bench_count" in first
    assert "case_types_count" in first

    # Benches
    benches = svc.get_benches()
    assert len(benches) > 0

    # Calcutta benches
    calcutta_benches = svc.get_benches("19~16")
    assert len(calcutta_benches) >= 3
    bench_names = [b["bench_key"] for b in calcutta_benches]
    assert any("jalpaiguri" in k for k in bench_names)

    # Case types for Delhi (7~26)
    delhi_types = svc.get_case_types("7~26", limit=10)
    assert len(delhi_types) > 0
    assert all(ct["court_code"] == "7~26" for ct in delhi_types)

    # Search case types with query
    arb_types = svc.get_case_types(q="bail", limit=10)
    assert len(arb_types) > 0

    # Search courts
    matches = svc.search_courts("Delhi")
    assert len(matches) >= 1
    assert any("Delhi" in m["court_name"] for m in matches)

def test_missing_dataset_fallback():
    # Service must not crash if dataset root is missing
    missing_svc = HighCourtMetadataService(dataset_root="/nonexistent/path/datasets")
    missing_svc.load()
    assert missing_svc.get_all_high_courts() == []
    assert missing_svc.get_benches() == []
    assert missing_svc.get_case_types() == []
    assert missing_svc.search_courts("Bombay") == []

def test_high_court_endpoints_require_auth():
    # Unauthorized requests should fail with 401
    resp = client.get("/api/v1/cases/high-courts")
    assert resp.status_code == 401

    resp_benches = client.get("/api/v1/cases/high-courts/benches")
    assert resp_benches.status_code == 401

    resp_types = client.get("/api/v1/cases/high-courts/9~13/case-types")
    assert resp_types.status_code == 401

def test_high_court_endpoints_authorized():
    # Sign up and log in
    client.post("/api/v1/auth/signup", json={
        "email": "hc_test@lexiai.com",
        "password": "Password123!",
        "full_name": "High Court Tester"
    })
    login_resp = client.post("/api/v1/auth/login", data={
        "username": "hc_test@lexiai.com",
        "password": "Password123!"
    })
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. List High Courts
    hc_resp = client.get("/api/v1/cases/high-courts", headers=headers)
    assert hc_resp.status_code == 200
    courts = hc_resp.json()
    assert len(courts) >= 25

    # 2. Search High Courts by query
    search_resp = client.get("/api/v1/cases/high-courts?q=Bombay", headers=headers)
    assert search_resp.status_code == 200
    b_courts = search_resp.json()
    assert any("Bombay" in c["court_name"] for c in b_courts)

    # 3. List Benches
    benches_resp = client.get("/api/v1/cases/high-courts/benches", headers=headers)
    assert benches_resp.status_code == 200
    assert len(benches_resp.json()) > 0

    # 4. List Case Types for Allahabad (9~13)
    types_resp = client.get("/api/v1/cases/high-courts/9~13/case-types?limit=5", headers=headers)
    assert types_resp.status_code == 200
    types = types_resp.json()
    assert len(types) == 5
    assert all("Allahabad" in t["court_name"] for t in types)
