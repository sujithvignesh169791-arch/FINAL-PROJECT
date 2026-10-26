from fastapi.testclient import TestClient
from app.main import app
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.models.user import User
import pytest
import uuid

Base.metadata.create_all(bind=engine)
client = TestClient(app)

def get_test_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_signup():
    email = f"test_{uuid.uuid4()}@example.com"
    response = client.post("/api/v1/auth/signup", json={"email": email, "password": "password123"})
    assert response.status_code == 200
    assert response.json()["email"] == email
    return email

def test_login():
    email = test_signup()
    response = client.post("/api/v1/auth/login", data={"username": email, "password": "password123"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    return response.json()["access_token"]

def test_login_invalid():
    response = client.post("/api/v1/auth/login", data={"username": "wrong@example.com", "password": "password123"})
    assert response.status_code == 401

def test_me():
    token = test_login()
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert "@example.com" in response.json()["email"]

def test_me_unauthorized():
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
