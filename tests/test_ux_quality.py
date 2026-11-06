from backend.config import settings
from backend.database.models import UXFeedback, UXRubricEvaluation, utcnow
from datetime import timedelta


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
    assert body["feedback"]["window_count"] == 1
    assert body["feedback"]["unique_respondents"] == 1
    assert body["feedback"]["workflow_breakdown"][0]["workflow"] == "Content Calendar"
    assert body["feedback"]["rows"][0]["user_id"] == "user-alpha"
    assert body["feedback"]["rows"][0]["comment"] == "Clear"
    assert body["combined_score"] is None
    assert body["score_status"] == "missing_rubric"


def test_rubric_score_and_combined_score(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "REQUIRE_AUTH", True)
    client.post("/auth/login", json={"username": "user-alpha", "api_key": "key-tenant-alpha"})
    for _ in range(4):
        client.post("/ux/feedback", json={"rating": 5, "workflow": "drafts"})
    client.post("/ux/feedback", json={"rating": 5, "workflow": "drafts"})
    client.post("/auth/login", json={"username": "admin-1", "api_key": "test-admin-key"})
    saved = client.post("/ux/rubric", json={
        "task_completion": 100, "workflow_efficiency": 80,
        "learnability": 80, "accessibility": 80, "interface_clarity": 60,
    })
    assert saved.status_code == 201
    assert saved.json()["rubric_score"] == 80
    dashboard = client.get("/ux/dashboard").json()
    assert dashboard["combined_score"] is None
    assert dashboard["score_status"] == "insufficient_feedback"
    assert dashboard["feedback"]["window_count"] == 5
    assert dashboard["feedback"]["unique_respondents"] == 1
    assert dashboard["feedback"]["workflow_breakdown"][0]["count"] == 5
    for index in range(2, 6):
        db_session.add(UXFeedback(id=f"distinct-rater-{index}", user_id=f"user-{index}", workspace_id="ws-alpha", rating=5, workflow="drafts", created_at=utcnow()))
    db_session.commit()
    dashboard = client.get("/ux/dashboard").json()
    assert dashboard["combined_score"] == 86
    assert dashboard["rubric"]["score"] == 80
    assert dashboard["feedback"]["window_count"] == 9
    assert dashboard["feedback"]["unique_respondents"] == 5
    assert dashboard["feedback"]["workflow_breakdown"][0]["respondents"] == 5


def test_empty_dashboard_and_legacy_workflow_aggregation(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "REQUIRE_AUTH", True)
    client.post("/auth/login", json={"username": "admin-1", "api_key": "test-admin-key"})
    empty = client.get("/ux/dashboard").json()
    assert empty["combined_score"] is None
    assert empty["feedback"]["average_rating"] is None
    assert empty["feedback"]["workflow_breakdown"] == []
    assert empty["feedback"]["trend"] == []

    db_session.add_all([
        UXFeedback(id="legacy-calendar", user_id="u1", workspace_id="system-admin", rating=4, workflow="Calendar", created_at=utcnow()),
        UXFeedback(id="canonical-calendar", user_id="u2", workspace_id="system-admin", rating=2, workflow="calendar", created_at=utcnow() - timedelta(days=1)),
        UXFeedback(id="old-feedback", user_id="u3", workspace_id="system-admin", rating=1, workflow="calendar", created_at=utcnow() - timedelta(days=120)),
    ])
    db_session.commit()
    summary = client.get("/ux/dashboard").json()["feedback"]
    assert summary["count"] == 3
    assert summary["window_count"] == 2
    assert summary["average_rating"] == 3
    assert summary["workflow_breakdown"] == [{"workflow": "Content Calendar", "average_rating": 3.0, "count": 2, "respondents": 2}]
    assert len(summary["trend"]) == 2


def test_feedback_rejects_unknown_workflow(client, monkeypatch):
    monkeypatch.setattr(settings, "REQUIRE_AUTH", True)
    client.post("/auth/login", json={"username": "user-alpha", "api_key": "key-tenant-alpha"})
    response = client.post("/ux/feedback", json={"rating": 4, "workflow": "Unregistered Workflow"})
    assert response.status_code == 422


def test_stale_rubric_is_not_combined_with_recent_feedback(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "REQUIRE_AUTH", True)
    client.post("/auth/login", json={"username": "user-alpha", "api_key": "key-tenant-alpha"})
    for _ in range(5):
        client.post("/ux/feedback", json={"rating": 5, "workflow": "analytics"})
    db_session.add(UXRubricEvaluation(
        id="stale-rubric", evaluator_id="system-admin", task_completion=100,
        workflow_efficiency=100, learnability=100, accessibility=100,
        interface_clarity=100, created_at=utcnow() - timedelta(days=120),
    ))
    db_session.commit()
    client.post("/auth/login", json={"username": "admin-1", "api_key": "test-admin-key"})
    dashboard = client.get("/ux/dashboard").json()
    assert dashboard["rubric"]["current_for_window"] is False
    assert dashboard["score_status"] == "stale_rubric"
    assert dashboard["combined_score"] is None


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
