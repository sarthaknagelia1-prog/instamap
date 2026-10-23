"""
tests/test_orchestrator.py

Tests for Phase 3 — Orchestrator Core:
- Decision engine rule evaluations (insufficient data, staleness, drop, steady)
- State machine execution and trace generation
- API endpoints: POST /creator-plan, GET /creator-plan/{job_id}, GET /creator-plan/history
"""

from datetime import datetime, timezone, timedelta
from backend.agents.schemas import DecisionThresholds, OrchestratorAction
from backend.orchestrator.decision_engine import evaluate_decision


def test_decision_engine_insufficient_posts():
    decision = evaluate_decision(
        total_posts=2,
        days_since_last_post=1,
        metrics={"average_engagement_rate": 5.0},
        trends={"recent_trend": "improving"},
        anomalies=[],
        thresholds=DecisionThresholds(min_posts_required=3),
    )
    assert decision.action == OrchestratorAction.REQUEST_MORE_DATA
    assert "Only 2 post(s) found" in decision.primary_reason


def test_decision_engine_stale_data():
    decision = evaluate_decision(
        total_posts=10,
        days_since_last_post=20,
        metrics={"average_engagement_rate": 4.5},
        trends={"recent_trend": "stable"},
        anomalies=[],
        thresholds=DecisionThresholds(max_staleness_days=14),
    )
    assert decision.action == OrchestratorAction.REQUEST_MORE_DATA
    assert "staleness threshold" in decision.primary_reason


def test_decision_engine_engagement_drop():
    decision = evaluate_decision(
        total_posts=15,
        days_since_last_post=2,
        metrics={"average_engagement_rate": 3.0},
        trends={"recent_trend": "declining", "week_over_week_delta_pct": -15.5},
        anomalies=[],
        thresholds=DecisionThresholds(engagement_drop_threshold_pct=-10.0),
    )
    assert decision.action == OrchestratorAction.GENERATE_FULL_PLAN
    assert any("fell by" in r for r in decision.reasons)


def test_decision_engine_healthy_momentum():
    decision = evaluate_decision(
        total_posts=20,
        days_since_last_post=1,
        metrics={"average_engagement_rate": 6.2},
        trends={"recent_trend": "improving", "week_over_week_delta_pct": 8.0},
        anomalies=[],
        thresholds=DecisionThresholds(),
    )
    assert decision.action == OrchestratorAction.REPORT_ONLY
    assert "improving" in decision.primary_reason


def test_api_creator_plan_flow(client):
    now = datetime.now(timezone.utc)
    # Ingest posts for a creator
    payload = {
        "creator_id": "creator_orch_test",
        "raw_data": [
            {
                "post_id": f"orch_p{i}",
                "date": (now - timedelta(days=5 - i)).isoformat(),
                "type": "reel" if i % 2 == 0 else "image",
                "likes": 200 + (i * 20),
                "comments": 20,
            }
            for i in range(5)
        ],
        "quality_threshold": 0.5,
    }
    ingest_res = client.post("/data/ingest", json=payload)
    assert ingest_res.status_code == 200

    # Execute POST /creator-plan
    plan_res = client.post(
        "/creator-plan",
        json={"creator_id": "creator_orch_test", "trigger_event": "manual"},
    )
    assert plan_res.status_code == 200
    plan_data = plan_res.json()

    assert plan_data["status"] == "completed"
    assert "job_id" in plan_data
    job_id = plan_data["job_id"]
    assert len(plan_data["execution_trace"]) >= 4  # fetch, analyze, decide, branch

    # Poll by job_id
    poll_res = client.get(f"/creator-plan/{job_id}")
    assert poll_res.status_code == 200
    assert poll_res.json()["job_id"] == job_id

    # Get history
    hist_res = client.get("/creator-plan/history/creator_orch_test")
    assert hist_res.status_code == 200
    history = hist_res.json()
    assert len(history) >= 1
    assert history[0]["job_id"] == job_id
