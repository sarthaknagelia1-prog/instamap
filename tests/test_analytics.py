"""
tests/test_analytics.py

Unit and integration tests for Phase 2 Performance Intelligence:
- backend.analytics.metrics
- backend.analytics.trends
- backend.analytics.anomalies
- backend.agents.analyst_agent
- POST /analyze-performance and GET /analytics/summary endpoints
"""

from datetime import datetime, timezone, timedelta
from backend.database.models import Creator, Post
from backend.analytics.metrics import (
    calculate_post_engagement_rate,
    calculate_post_metrics,
    calculate_aggregate_metrics,
)
from backend.analytics.trends import detect_trends, find_best_posting_window
from backend.analytics.anomalies import detect_anomalies
from backend.agents.analyst_agent import run_analyst_agent


def test_post_engagement_rate():
    post = {
        "likes_count": 100,
        "comments_count": 20,
        "shares_count": 10,
        "saves_count": 30,
        "reach": 1000,
    }
    # Total interactions: 160. Reach: 1000. ER = (160 / 1000) * 100 = 16.0%
    er = calculate_post_engagement_rate(post)
    assert er == 16.0


def test_post_metrics_breakdown():
    post = {
        "likes_count": 50,
        "comments_count": 10,
        "shares_count": 5,
        "saves_count": 15,
        "reach": 500,
        "impressions": 800,
    }
    metrics = calculate_post_metrics(post)
    assert metrics["engagement_rate"] == 16.0
    assert metrics["save_rate"] == 3.0  # (15 / 500) * 100
    assert metrics["share_rate"] == 1.0  # (5 / 500) * 100
    assert metrics["reach_efficiency"] == 62.5  # (500 / 800) * 100


def test_aggregate_metrics():
    posts = [
        {"post_id": "p1", "content_type": "reel", "likes_count": 200, "comments_count": 20, "reach": 1000}, # ER: 22.0%
        {"post_id": "p2", "content_type": "reel", "likes_count": 150, "comments_count": 10, "reach": 1000}, # ER: 16.0%
        {"post_id": "p3", "content_type": "image", "likes_count": 30, "comments_count": 5, "reach": 1000},  # ER: 3.5%
    ]
    agg = calculate_aggregate_metrics(posts)
    assert agg["total_posts"] == 3
    assert agg["top_content_type"] == "reel"
    assert "reel" in agg["content_type_breakdown"]
    assert "image" in agg["content_type_breakdown"]
    assert agg["content_type_breakdown"]["reel"]["count"] == 2
    assert agg["content_type_breakdown"]["image"]["count"] == 1
    assert len(agg["top_performing_posts"]) == 3
    assert agg["top_performing_posts"][0]["post_id"] == "p1"


def test_detect_trends_improving():
    base_time = datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc)
    # Earlier posts lower ER, later posts higher ER
    posts = [
        {"post_id": "p1", "timestamp": (base_time - timedelta(days=12)).isoformat(), "reach": 1000, "likes_count": 20, "comments_count": 5}, # 2.5%
        {"post_id": "p2", "timestamp": (base_time - timedelta(days=10)).isoformat(), "reach": 1000, "likes_count": 30, "comments_count": 5}, # 3.5%
        {"post_id": "p3", "timestamp": (base_time - timedelta(days=3)).isoformat(), "reach": 1000, "likes_count": 100, "comments_count": 10}, # 11.0%
        {"post_id": "p4", "timestamp": base_time.isoformat(), "reach": 1000, "likes_count": 150, "comments_count": 20}, # 17.0%
    ]
    trend_data = detect_trends(posts)
    assert trend_data["recent_trend"] == "improving"
    assert trend_data["week_over_week_delta_pct"] > 5.0
    assert len(trend_data["rolling_average_er"]) == 4


def test_find_best_posting_window():
    # Wednesday 19:00 UTC with high engagement
    t_wed_1 = datetime(2026, 8, 5, 19, 30, tzinfo=timezone.utc) # 2026-08-05 was Wednesday
    t_wed_2 = datetime(2026, 8, 12, 20, 00, tzinfo=timezone.utc)
    t_mon = datetime(2026, 8, 3, 10, 00, tzinfo=timezone.utc) # Monday

    posts = [
        {"post_id": "p1", "timestamp": t_wed_1.isoformat(), "reach": 1000, "likes_count": 300, "comments_count": 50}, # 35%
        {"post_id": "p2", "timestamp": t_wed_2.isoformat(), "reach": 1000, "likes_count": 250, "comments_count": 40}, # 29%
        {"post_id": "p3", "timestamp": t_mon.isoformat(), "reach": 1000, "likes_count": 20, "comments_count": 2}, # 2.2%
    ]
    window = find_best_posting_window(posts)
    assert "Wednesday" in window
    assert "18:00 - 21:00 UTC" in window


def test_detect_anomalies_spike_and_drop():
    posts = [
        {"post_id": "norm1", "reach": 1000, "likes_count": 50, "comments_count": 5}, # 5.5%
        {"post_id": "norm2", "reach": 1000, "likes_count": 52, "comments_count": 6}, # 5.8%
        {"post_id": "norm3", "reach": 1000, "likes_count": 48, "comments_count": 4}, # 5.2%
        {"post_id": "norm4", "reach": 1000, "likes_count": 51, "comments_count": 5}, # 5.6%
        {"post_id": "spike_post", "reach": 1000, "likes_count": 400, "comments_count": 80}, # 48.0% (huge spike)
        {"post_id": "drop_post", "reach": 1000, "likes_count": 1, "comments_count": 0}, # 0.1% (drop)
    ]
    anomalies = detect_anomalies(posts)
    flagged_ids = [a["post_id"] for a in anomalies]
    assert "spike_post" in flagged_ids
    assert "drop_post" in flagged_ids


def test_api_analyze_performance(client, db_session):
    # Setup test creator and posts
    creator = Creator(id="cr_perf_test")
    db_session.add(creator)
    db_session.commit()

    p1 = Post(
        creator_id="cr_perf_test",
        post_id="post_101",
        content_type="reel",
        timestamp=datetime(2026, 8, 1, 18, 0, tzinfo=timezone.utc),
        likes_count=120,
        comments_count=15,
        reach=1000,
    )
    p2 = Post(
        creator_id="cr_perf_test",
        post_id="post_102",
        content_type="carousel",
        timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=timezone.utc),
        likes_count=40,
        comments_count=5,
        reach=1000,
    )
    db_session.add_all([p1, p2])
    db_session.commit()

    # Call POST /analyze-performance
    resp = client.post("/analyze-performance", json={"creator_id": "cr_perf_test"})
    assert resp.status_code == 200
    data = resp.json()

    assert data["creator_id"] == "cr_perf_test"
    assert data["top_content_type"] == "reel"
    assert data["average_engagement_rate"] > 0
    assert "recommended_action" in data
    assert "best_posting_window" in data
    assert "recent_trend" in data

    # Verify engagement_rate was persisted on Post records
    db_session.refresh(p1)
    assert p1.engagement_rate == 13.5  # (135 / 1000) * 100

    # Call GET /analytics/summary
    sum_resp = client.get("/analytics/summary?creator_id=cr_perf_test")
    assert sum_resp.status_code == 200
    sum_data = sum_resp.json()
    assert sum_data["total_posts"] == 2
    assert sum_data["top_content_type"] == "reel"
