from backend.config import settings


def test_feedback_is_identified_and_admin_dashboard_is_protected(client, monkeypatch):
    monkeypatch.setattr(settings, "REQUIRE_AUTH", True)
    user = client.post("/auth/login", json={"username": "user-alpha", "api_key": "key-tenant-alpha"})
    assert user.status_code == 200
    saved = client.post("/ux/feedback", json={"rating": 4, "workflow": "Calendar", "comment": "Clear"})
    assert saved.status_code == 201
    assert client.get("/ux/dashboard").status_code == 403

    admin = client.post("/auth/login", json={"username": "admin-1", "api_key": "test-admin-key"})
    assert admin.status_code == 200
    dashboard = client.get("/ux/dashboard")
    assert dashboard.status_code == 200
    body = dashboard.json()
    assert body["feedback"]["count"] == 1
    assert body["feedback"]["rows"][0]["user_id"] == "user-alpha"
    assert body["feedback"]["rows"][0]["comment"] == "Clear"
    assert body["combined_score"] is None


def test_rubric_score_and_combined_score(client, monkeypatch):
    monkeypatch.setattr(settings, "REQUIRE_AUTH", True)
    client.post("/auth/login", json={"username": "user-alpha", "api_key": "key-tenant-alpha"})
    client.post("/ux/feedback", json={"rating": 5, "workflow": "Drafts"})
    client.post("/auth/login", json={"username": "admin-1", "api_key": "test-admin-key"})
    saved = client.post("/ux/rubric", json={
        "task_completion": 100, "workflow_efficiency": 80,
        "learnability": 80, "accessibility": 80, "interface_clarity": 60,
    })
    assert saved.status_code == 201
    assert saved.json()["rubric_score"] == 80
    dashboard = client.get("/ux/dashboard").json()
    assert dashboard["combined_score"] == 86
    assert dashboard["rubric"]["score"] == 80


def test_production_rejects_passwordless_login_and_builtin_demo_credentials(client, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "REQUIRE_AUTH", False)
    monkeypatch.setattr(settings, "API_KEYS_RAW", '{"prod-owner-key":{"user_id":"prod-owner","workspace_id":"default","role":"admin"}}')
    assert client.post("/auth/login", json={"username": "anyone"}).status_code == 401
    assert client.post("/auth/login", json={"username": "demo", "api_key": "test-admin-key"}).status_code == 401
    assert client.get("/auth/me").status_code == 401
    login = client.post("/auth/login", json={"username": "prod-owner", "api_key": "prod-owner-key"})
    assert login.status_code == 200
    assert "; secure" in login.headers["set-cookie"].lower()
    assert client.get("/auth/me", headers={"X-API-Key": "prod-owner-key"}).json()["user_id"] == "prod-owner"


def test_non_development_environment_rejects_passwordless_login(client, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "staging")
    monkeypatch.setattr(settings, "REQUIRE_AUTH", False)
    assert client.post("/auth/login", json={"username": "anyone"}).status_code == 401
    assert client.post("/auth/login", json={"username": "demo", "api_key": "key-tenant-alpha"}).status_code == 401
