"""
tests/test_auth_routes.py

Test suite for authentication routes: login, token validation, user context, and logout.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_login_with_valid_admin_key():
    payload = {
        "username": "admin-1",
        "api_key": "test-admin-key",
    }
    resp = client.post("/auth/login", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == "admin-1"
    assert data["role"] == "system_admin"
    assert data["workspace_id"] == "system-admin"
    assert "access_token" not in data
    assert resp.cookies.get("instamap_session")
    assert "httponly" in resp.headers.get("set-cookie", "").lower()


def test_login_with_tenant_key():
    payload = {
        "username": "user-alpha",
        "workspace_id": "ws-alpha",
        "api_key": "key-tenant-alpha",
    }
    resp = client.post("/auth/login", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == "user-alpha"
    assert data["workspace_id"] == "ws-alpha"
    assert data["role"] == "member"


def test_login_with_invalid_key_fails():
    payload = {
        "username": "attacker",
        "api_key": "totally_invalid_secret_key",
    }
    resp = client.post("/auth/login", json=payload)
    assert resp.status_code == 401
    assert "Invalid API key" in resp.json()["detail"]


def test_login_demo_mode_ephemeral_token():
    payload = {
        "username": "creator_sarthak",
        "workspace_id": "creator_studio",
    }
    resp = client.post("/auth/login", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == "creator_sarthak"
    assert data["workspace_id"] == "creator_studio"
    assert "access_token" not in data
    assert resp.cookies.get("instamap_session")
    assert client.get("/auth/me").json()["user_id"] == "creator_sarthak"


def test_get_me_with_bearer_token():
    # Login first
    login_resp = client.post("/auth/login", json={"username": "user-alpha", "api_key": "key-tenant-alpha"})
    assert login_resp.status_code == 200
    me_resp = client.get("/auth/me")
    assert me_resp.status_code == 200
    data = me_resp.json()
    assert data["user_id"] == "user-alpha"
    assert data["workspace_id"] == "ws-alpha"


def test_logout():
    login = client.post("/auth/login", json={"username": "user-alpha", "api_key": "key-tenant-alpha"})
    assert login.status_code == 200
    resp = client.post("/auth/logout")
    assert resp.status_code == 200
    assert resp.json()["status"] == "logged_out"
    assert client.get("/auth/me").json()["is_authenticated"] is False
