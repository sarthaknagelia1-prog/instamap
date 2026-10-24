"""
tests/test_virality.py

Unit and endpoint test suite for the Virality ML Layer.
"""

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.analytics.virality import ViralityPredictor
from backend.database.session import SessionLocal
from backend.database.models import Creator, Post, TrendingSignal

client = TestClient(app)


def test_hook_evaluation_high_converting():
    hook = "3 secret mistakes why most creators never scale on Instagram?"
    score, feedback, recs = ViralityPredictor.evaluate_hook(hook)
    assert score >= 18.0
    assert "Hook score:" in feedback


def test_hook_evaluation_weak():
    hook = "Hi guys"
    score, feedback, recs = ViralityPredictor.evaluate_hook(hook)
    assert score < 12.0
    assert len(recs) > 0


def test_format_evaluation():
    hist = [
        {"content_type": "REEL", "engagement_rate": 8.5},
        {"content_type": "REEL", "engagement_rate": 9.2},
        {"content_type": "IMAGE", "engagement_rate": 3.1},
    ]
    score_reel, _, _ = ViralityPredictor.evaluate_format("REEL", hist)
    score_image, _, _ = ViralityPredictor.evaluate_format("IMAGE", hist)
    assert score_reel > score_image


def test_save_share_cta_evaluation():
    caption = (
        "Here are the exact 3 steps to double your Instagram reach:\n"
        "1. Hook in the first 2 seconds.\n"
        "2. Deliver high value in the middle.\n"
        "3. Clear CTA at the end.\n\n"
        "👉 Save this post for later so you can reference it!"
    )
    score, feedback, recs = ViralityPredictor.evaluate_save_share_cta(caption)
    assert score >= 15.0
    assert "Save/Share friction:" in feedback


def test_virality_predictor_end_to_end():
    res = ViralityPredictor.predict(
        hook="The truth about why most creators fail with video copy?",
        caption="Here are the top 3 frameworks you should use. Save this for later!",
        content_type="REEL",
        scheduled_time=datetime(2026, 10, 28, 18, 0, tzinfo=timezone.utc),
        hashtags=["#creator", "#growth"],
        historical_posts=[
            {"post_id": "p1", "content_type": "REEL", "reach": 2500, "engagement_rate": 6.2, "timestamp": "2026-10-15T18:00:00Z"},
            {"post_id": "p2", "content_type": "CAROUSEL", "reach": 1800, "engagement_rate": 5.1, "timestamp": "2026-10-18T19:00:00Z"},
        ],
        active_trends=["video copy", "content framework"],
    )

    assert "virality_score" in res
    assert 0 <= res["virality_score"] <= 100
    assert "tier" in res
    assert "predicted_reach_multiplier" in res
    assert res["predicted_reach_multiplier"] >= 0.5
    assert "predicted_reach_range" in res
    assert res["predicted_reach_range"]["min_reach"] <= res["predicted_reach_range"]["median_reach"]
    assert "category_scores" in res
    assert "actionable_recommendations" in res


def test_predict_virality_endpoint():
    db = SessionLocal()
    c_id = "virality_test_creator"
    try:
        if not db.get(Creator, c_id):
            db.add(Creator(id=c_id, workspace_id="default"))
            db.commit()

        payload = {
            "creator_id": c_id,
            "hook": "Stop making this viral hook mistake in 2026",
            "caption": "Step by step breakdown. Save this for reference!\n- Step 1\n- Step 2",
            "content_type": "REEL",
            "hashtags": ["#marketing", "#socialmedia"],
        }
        resp = client.post("/analytics/predict-virality", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["creator_id"] == c_id
        assert "virality_score" in data
        assert "tier" in data
        assert "category_scores" in data
    finally:
        db.close()
