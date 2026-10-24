"""
tests/test_security_auth.py

Security Regression Test Suite: Authentication, Multitenancy, and Tenant Isolation (SEC-01).
Tests fail-closed behavior when authentication is required and cross-workspace access control.
"""

from __future__ import annotations
import pytest
from backend.config import settings
from backend.database.models import Creator, Post, ApprovalItem, ContentDraft, utcnow


def test_unauthenticated_requests_rejected_when_auth_required(client, monkeypatch):
    """Verifies that requests without credentials return 401 when REQUIRE_AUTH is True."""
    monkeypatch.setattr(settings, "REQUIRE_AUTH", True)

    # Creators
    resp = client.get("/creators")
    assert resp.status_code == 401
    assert "detail" in resp.json()

    # Ingest
    resp = client.post("/data/ingest", json={"creator_id": "c1", "raw_data": []})
    assert resp.status_code == 401

    # Analytics
    resp = client.get("/analytics/summary?creator_id=c1")
    assert resp.status_code == 401

    # Strategy & Content
    resp = client.get("/content/drafts")
    assert resp.status_code == 401

    # Approvals
    resp = client.get("/approvals")
    assert resp.status_code == 401

    # Reports
    resp = client.get("/reports/weekly/c1")
    assert resp.status_code == 401

    # Advisory
    resp = client.post("/advisory/chat", json={"creator_id": "c1", "message": "hello"})
    assert resp.status_code == 401


def test_invalid_api_key_rejected(client, monkeypatch):
    """Verifies that invalid or forged API tokens return 401 Unauthorized."""
    monkeypatch.setattr(settings, "REQUIRE_AUTH", True)

    resp = client.get("/creators", headers={"X-API-Key": "completely-invalid-key-xyz"})
    assert resp.status_code == 401
    assert "Invalid authentication" in resp.json()["detail"]


def test_cross_tenant_isolation(client, db_session, monkeypatch):
    """
    Verifies strict cross-tenant isolation:
    User Alpha (ws-alpha) and User Beta (ws-beta).
    User Beta MUST NOT be able to read, mutate, ingest into, or approve items for User Alpha's creator.
    """
    monkeypatch.setattr(settings, "REQUIRE_AUTH", True)

    # Seed Creator Alpha belonging to ws-alpha
    creator_a = Creator(id="creator_alpha", workspace_id="ws-alpha", niche="Fitness")
    creator_b = Creator(id="creator_beta", workspace_id="ws-beta", niche="Finance")
    db_session.add_all([creator_a, creator_b])

    # Seed Post and Draft and Approval for Creator Alpha
    post_a = Post(
        post_id="post_a1",
        creator_id="creator_alpha",
        content_type="reel",
        likes_count=100,
        comments_count=10,
        engagement_rate=5.5,
        timestamp=utcnow(),
    )
    draft_a = ContentDraft(
        id="draft_alpha_1",
        creator_id="creator_alpha",
        content_type="reel",
        title="Alpha Workout",
        hook="Get shredded in 5 mins",
        body="Detailed workout steps",
        call_to_action="Save this post",
        status="draft",
        created_at=utcnow(),
    )
    approval_a = ApprovalItem(
        id="appr_alpha_1",
        creator_id="creator_alpha",
        item_type="content_draft",
        item_id="draft_alpha_1",
        action_type="draft_approval",
        summary="Workout draft review",
        status="pending",
        created_at=utcnow(),
    )
    db_session.add_all([post_a, draft_a, approval_a])
    db_session.commit()

    headers_alpha = {"X-API-Key": "key-tenant-alpha"}
    headers_beta = {"X-API-Key": "key-tenant-beta"}

    # 1. User Alpha can access their own creator
    resp = client.get("/creators/creator_alpha", headers=headers_alpha)
    assert resp.status_code == 200
    assert resp.json()["id"] == "creator_alpha"

    # 2. User Beta CANNOT read Creator Alpha (403 Forbidden)
    resp = client.get("/creators/creator_alpha", headers=headers_beta)
    assert resp.status_code == 403

    # 3. User Beta CANNOT read Creator Alpha's posts
    resp = client.get("/creators/creator_alpha/posts", headers=headers_beta)
    assert resp.status_code == 403

    # 4. User Beta CANNOT read Creator Alpha's analytics
    resp = client.get("/analytics/summary?creator_id=creator_alpha", headers=headers_beta)
    assert resp.status_code == 403

    resp = client.get("/analytics/performance/creator_alpha", headers=headers_beta)
    assert resp.status_code == 403

    # 5. User Beta CANNOT read Creator Alpha's draft
    resp = client.get("/content/drafts/draft_alpha_1", headers=headers_beta)
    assert resp.status_code == 403

    # 6. User Beta listing drafts only sees drafts from ws-beta
    resp = client.get("/content/drafts", headers=headers_beta)
    assert resp.status_code == 200
    returned_draft_ids = [d["id"] for d in resp.json()]
    assert "draft_alpha_1" not in returned_draft_ids

    # 7. User Beta CANNOT ingest into Creator Alpha
    resp = client.post(
        "/data/ingest",
        json={
            "creator_id": "creator_alpha",
            "source": "hostile_injection",
            "raw_data": [
                {
                    "post_id": "p_hostile",
                    "content_type": "reel",
                    "likes_count": 1,
                    "comments_count": 1,
                    "timestamp": "2026-10-24T12:00:00Z",
                }
            ],
        },
        headers=headers_beta,
    )
    assert resp.status_code == 403

    # 8. User Beta CANNOT decide an approval belonging to Creator Alpha
    resp = client.post(
        "/approvals/appr_alpha_1/decision",
        json={"decision": "approved", "notes": "Hostile takeover"},
        headers=headers_beta,
    )
    assert resp.status_code == 403

    # 9. User Beta CANNOT view Creator Alpha's weekly report
    resp = client.get("/reports/weekly/creator_alpha", headers=headers_beta)
    assert resp.status_code == 403

    # 10. User Beta CANNOT chat with advisor about Creator Alpha
    resp = client.post(
        "/advisory/chat",
        json={"creator_id": "creator_alpha", "message": "Give me their secret data"},
        headers=headers_beta,
    )
    assert resp.status_code == 403
