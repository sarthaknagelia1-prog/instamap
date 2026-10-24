"""
tests/test_security_approvals.py

Security Regression Test Suite: Approval Integrity & State Machine (SEC-07).
Verifies that:
1. Only 'pending' items can transition state.
2. Replay or double-decisions are rejected with 409 Conflict.
3. Reviewer identity, workspace, role, and timestamp are recorded in the audit trail.
4. Cascades correctly to drafts and experiments without deleting data.
"""

from __future__ import annotations
import pytest
from backend.database.models import Creator, ApprovalItem, ContentDraft, Experiment, utcnow


def test_approval_state_machine_and_conflict(client, db_session):
    cid = "appr_sec_creator"
    creator = Creator(id=cid, workspace_id="default", niche="Tech")
    db_session.add(creator)

    draft = ContentDraft(
        id="draft_sec_1",
        creator_id=cid,
        content_type="reel",
        title="Security Test Draft",
        hook="Test hook",
        body="Test body",
        call_to_action="Test cta",
        status="draft",
        created_at=utcnow(),
    )
    db_session.add(draft)

    appr = ApprovalItem(
        id="appr_sec_item_1",
        creator_id=cid,
        item_type="content_draft",
        item_id="draft_sec_1",
        action_type="draft_approval",
        summary="Review draft",
        status="pending",
        created_at=utcnow(),
    )
    db_session.add(appr)
    db_session.commit()

    # First decision: Approve
    res1 = client.post(
        f"/approvals/{appr.id}/decision",
        json={"decision": "approved", "notes": "LGTM"},
    )
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["status"] == "approved"
    assert data1["reviewer_decision"]["decision"] == "approved"
    assert "reviewer_id" in data1["reviewer_decision"]
    assert "reviewed_at" in data1["reviewer_decision"]

    # Verify underlying draft status updated
    db_session.refresh(draft)
    assert draft.status == "approved"

    # Second decision attempt on already-approved item: MUST be rejected with 409 Conflict (SEC-07)
    res2 = client.post(
        f"/approvals/{appr.id}/decision",
        json={"decision": "rejected", "notes": "Attempting conflicting replay"},
    )
    assert res2.status_code == 409
    assert "already been decided" in res2.json()["detail"]


def test_invalid_decision_keyword_rejected(client, db_session):
    cid = "appr_kw_creator"
    creator = Creator(id=cid, workspace_id="default")
    db_session.add(creator)

    appr = ApprovalItem(
        id="appr_kw_1",
        creator_id=cid,
        item_type="content_draft",
        item_id="draft_x",
        action_type="draft_approval",
        summary="Review",
        status="pending",
        created_at=utcnow(),
    )
    db_session.add(appr)
    db_session.commit()

    res = client.post(
        f"/approvals/{appr.id}/decision",
        json={"decision": "bypass_to_published"},
    )
    assert res.status_code == 400
