"""
tests/test_simulation.py

Unit and endpoint test suite for the Growth & Post Simulation Layer.
"""

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.analytics.simulation import GrowthSimulator
from backend.database.session import SessionLocal
from backend.database.models import Creator, Post

client = TestClient(app)


def test_growth_simulator_monte_carlo():
    posts = [
        {"post_id": f"p_{i}", "reach": 1000 + i * 150, "engagement_rate": 5.0, "timestamp": f"2026-09-0{i+1}T18:00:00Z"}
        for i in range(8)
    ]
    res = GrowthSimulator.simulate_growth(posts, days=30, iterations=50, seed=123)

    assert res["simulation_days"] == 30
    assert len(res["timeline"]) == 30
    summary = res["summary"]
    assert "baseline" in summary
    assert "recommended" in summary
    assert "aggressive" in summary
    assert summary["recommended"]["projected_reach"] >= summary["baseline"]["projected_reach"]
    assert len(res["strategic_takeaways"]) > 0


def test_simulate_post_reach():
    posts = [
        {"post_id": f"p_{i}", "reach": 1500, "engagement_rate": 6.0}
        for i in range(5)
    ]
    res = GrowthSimulator.simulate_post(
        hook="3 hacks to 10x your audience retention",
        caption="Save this for your next Reel planning session!",
        content_type="REEL",
        historical_posts=posts,
        draws=100,
        seed=42,
    )

    assert "virality_evaluation" in res
    assert "simulation_stats" in res
    stats = res["simulation_stats"]
    pcts = stats["percentiles"]
    assert pcts["p10_conservative"] <= pcts["p50_expected_median"] <= pcts["p90_viral_upside"]
    assert len(res["distribution_bins"]) == 10


def test_simulation_endpoints():
    db = SessionLocal()
    c_id = "sim_test_creator"
    try:
        if not db.get(Creator, c_id):
            db.add(Creator(id=c_id, workspace_id="default"))
            db.commit()

        # Growth simulation endpoint
        growth_payload = {
            "creator_id": c_id,
            "days": 30,
            "iterations": 30,
        }
        resp = client.post("/analytics/simulation/growth", json=growth_payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["creator_id"] == c_id
        assert len(data["timeline"]) == 30
        assert "summary" in data

        # Single post simulation endpoint
        post_payload = {
            "creator_id": c_id,
            "hook": "Why 99% of creators fail at consistency",
            "caption": "Full framework below. Save this post for reference!",
            "content_type": "REEL",
            "draws": 100,
        }
        resp2 = client.post("/analytics/simulation/post", json=post_payload)
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert data2["creator_id"] == c_id
        assert "simulation_stats" in data2
        assert "distribution_bins" in data2
    finally:
        db.close()
