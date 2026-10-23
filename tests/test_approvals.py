"""
tests/test_approvals.py

Phase 6 Tests: Approval & Review Layer:
- Action Classifier rules (auto-approve vs review-required)
- Event Bus pub/sub messaging
- Approval queue lifecycle: approve cascades to underlying draft
- Approval rejection archives rather than deletes (audit integrity)
- Mark published tracking flow
- Approval stats and REST endpoints
"""

from datetime import datetime, timezone
from backend.approvals.classifier import classify_action
from backend.approvals.events import EventBus
from backend.database.models import Creator, ContentDraft, ApprovalItem, utcnow


def test_action_classifier_rules():
    # Passive/diagnostic actions should auto-approve
    res_report = classify_action("report_only")
    assert res_report["auto_approve"] is True
    assert res_report["requires_review"] is False
    assert res_report["risk_level"] == "low"

    res_trends = classify_action("sniff_trends")
    assert res_trends["auto_approve"] is True
    assert res_trends["requires_review"] is False

    # Creative / high-stakes actions must require review
    res_draft = classify_action("draft_approval", item_type="content_draft")
    assert res_draft["requires_review"] is True
    assert res_draft["auto_approve"] is False
    assert res_draft["risk_level"] == "high"

    res_strat = classify_action("strategy_pivot", item_type="strategy")
    assert res_strat["requires_review"] is True
    assert res_strat["risk_level"] == "medium"

    res_exp = classify_action("experiment_launch", item_type="experiment")
    assert res_exp["requires_review"] is True


def test_event_bus_pub_sub():
    bus = EventBus()
    received = []

    def on_approval(data):
        received.append(data)

    bus.subscribe("approval.created", on_approval)
    bus.publish("approval.created", {"id": "appr_123", "status": "pending"})

    assert len(received) == 1
    assert received[0]["id"] == "appr_123"

    # Test clear
    bus.clear()
    bus.publish("approval.created", {"id": "appr_456"})
    assert len(received) == 1


def test_approval_queue_lifecycle_approve(client):
    creator_id = "creator_appr_1"

    # 1. Ingest dummy creator data and generate content draft
    client.post("/data/ingest", json={
        "creator_id": creator_id,
        "raw_data": [
            {"post_id": "p_appr_1", "date": "2026-10-01T12:00:00Z", "type": "reel", "likes": 50, "comments": 5, "reach": 1000},
            {"post_id": "p_appr_2", "date": "2026-10-03T12:00:00Z", "type": "reel", "likes": 60, "comments": 6, "reach": 1200},
            {"post_id": "p_appr_3", "date": "2026-10-05T12:00:00Z", "type": "reel", "likes": 55, "comments": 4, "reach": 1100},
        ],
    })

    drafts_res = client.post("/content/generate", json={
        "creator_id": creator_id,
        "custom_item": {"content_type": "reel", "theme": "AI Productivity"},
    })
    assert drafts_res.status_code == 200
    draft_id = drafts_res.json()[0]["id"]

    # 2. Verify draft was automatically enqueued in approval_queue
    appr_res = client.get(f"/approvals?creator_id={creator_id}&status=pending")
    assert appr_res.status_code == 200
    items = appr_res.json()
    assert len(items) >= 1
    appr_id = next(i["id"] for i in items if i["item_id"] == draft_id)

    # 3. Approve via POST /approvals/{id}/decision
    decision_res = client.post(f"/approvals/{appr_id}/decision", json={
        "decision": "approved",
        "notes": "Looks solid, approved for filming.",
    })
    assert decision_res.status_code == 200
    appr_data = decision_res.json()
    assert appr_data["status"] == "approved"
    assert appr_data["reviewer_decision"]["decision"] == "approved"

    # 4. Verify status cascaded to the underlying ContentDraft
    draft_check = client.get(f"/content/drafts/{draft_id}")
    assert draft_check.status_code == 200
    assert draft_check.json()["status"] == "approved"


def test_approval_rejection_archives_not_deletes(client):
    creator_id = "creator_appr_reject"

    client.post("/data/ingest", json={
        "creator_id": creator_id,
        "raw_data": [
            {"post_id": "p_rej_1", "date": "2026-10-01T12:00:00Z", "type": "carousel", "likes": 30, "comments": 2, "reach": 800},
            {"post_id": "p_rej_2", "date": "2026-10-03T12:00:00Z", "type": "carousel", "likes": 35, "comments": 3, "reach": 850},
            {"post_id": "p_rej_3", "date": "2026-10-05T12:00:00Z", "type": "carousel", "likes": 32, "comments": 1, "reach": 820},
        ],
    })

    drafts_res = client.post("/content/generate", json={
        "creator_id": creator_id,
        "custom_item": {"content_type": "carousel", "theme": "Off-brand angle"},
    })
    draft_id = drafts_res.json()[0]["id"]

    # Locate approval item
    appr_res = client.get(f"/approvals?creator_id={creator_id}&status=pending")
    appr_id = next(i["id"] for i in appr_res.json() if i["item_id"] == draft_id)

    # Reject item with reason
    reject_res = client.post(f"/approvals/{appr_id}/decision", json={
        "decision": "rejected",
        "rejection_reason": "Topic angle does not fit our Q4 positioning.",
    })
    assert reject_res.status_code == 200
    assert reject_res.json()["status"] == "rejected"

    # Confirm underlying ContentDraft is archived, NOT deleted
    draft_check = client.get(f"/content/drafts/{draft_id}")
    assert draft_check.status_code == 200
    assert draft_check.json()["status"] == "archived"


def test_mark_published_flow(client):
    creator_id = "creator_pub_test"

    client.post("/data/ingest", json={
        "creator_id": creator_id,
        "raw_data": [
            {"post_id": "p_pub_1", "date": "2026-10-01T12:00:00Z", "type": "reel", "likes": 40, "comments": 4, "reach": 900},
            {"post_id": "p_pub_2", "date": "2026-10-02T12:00:00Z", "type": "reel", "likes": 42, "comments": 5, "reach": 920},
            {"post_id": "p_pub_3", "date": "2026-10-03T12:00:00Z", "type": "reel", "likes": 41, "comments": 3, "reach": 910},
        ],
    })

    # Generate draft and approve it
    draft_res = client.post("/content/generate", json={
        "creator_id": creator_id,
        "custom_item": {"content_type": "reel", "theme": "Reel Hook Testing"},
    })
    draft_id = draft_res.json()[0]["id"]

    # Mark as published with actual Instagram post ID
    pub_res = client.post(f"/content/drafts/{draft_id}/mark-published", json={
        "published_post_id": "instagram_live_post_999",
    })
    assert pub_res.status_code == 200
    data = pub_res.json()
    assert data["status"] == "published"
    assert data["published_post_id"] == "instagram_live_post_999"
    assert data["published_at"] is not None


def test_approval_stats_endpoint(client):
    creator_id = "creator_stats_test"

    # Query stats for creator
    res = client.get(f"/approvals/stats/{creator_id}")
    assert res.status_code == 200
    stats = res.json()
    assert stats["creator_id"] == creator_id
    assert "pending_count" in stats
    assert "approval_rate_pct" in stats
