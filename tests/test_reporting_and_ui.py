"""
tests/test_reporting_and_ui.py

Phase 7 Tests: Reporting, Polish & Creator Web Dashboard UI:
- Weekly executive growth report generation (JSON, Markdown, standalone HTML)
- REST endpoints for weekly reports (GET /reports/weekly/{id}, GET /reports/weekly/{id}/html)
- Single-session onboarding pipeline (POST /onboarding/initiate)
- Dashboard UI SPA serving (GET / and GET /dashboard)
"""

from datetime import datetime, timezone
import pytest
from backend.database.models import Creator, Post, Strategy, ContentPlan, Experiment, utcnow
from backend.reporting.weekly_report import generate_weekly_report


def test_generate_weekly_report_structure(db_session):
    cid = "rep_test_creator"
    creator = Creator(id=cid, niche="Personal Finance")
    db_session.add(creator)

    # Add sample posts
    p1 = Post(
        post_id="rep_p1",
        creator_id=cid,
        content_type="reel",
        likes_count=500,
        comments_count=40,
        shares_count=100,
        saves_count=150,
        reach=5000,
        impressions=6000,
        engagement_rate=15.8,
        timestamp=utcnow(),
    )
    p2 = Post(
        post_id="rep_p2",
        creator_id=cid,
        content_type="carousel",
        likes_count=300,
        comments_count=20,
        shares_count=50,
        saves_count=80,
        reach=3000,
        impressions=4000,
        engagement_rate=15.0,
        timestamp=utcnow(),
    )
    db_session.add_all([p1, p2])

    # Add sample strategy and content plan
    strat = Strategy(
        id="rep_s1",
        creator_id=cid,
        primary_content_type="reel",
        format_allocation={"reel": 70, "carousel": 30},
        core_pillars=["Index Funds", "Budgeting Hacks"],
        strategic_priorities=["Maximize shareability"],
    )
    plan = ContentPlan(
        id="rep_cp1",
        creator_id=cid,
        scheduled_items=[
            {
                "day": "Monday",
                "content_type": "reel",
                "scheduled_time": "18:00 UTC",
                "theme": "Index Funds",
                "concept_angle": "How $100/mo grows to $100k",
                "hook_preview": "Stop saving money in a savings account",
                "target_metric": "shares",
            }
        ],
    )
    exp = Experiment(
        id="rep_exp1",
        creator_id=cid,
        title="Negative Framing Hook Test",
        hypothesis="Negative framing boosts reach",
        metric_target="reach",
        status="completed_conclusive",
        evaluation_result={"winner": "variant", "confidence_pct": 96.5, "p_value": 0.035},
    )
    db_session.add_all([strat, plan, exp])
    db_session.commit()

    report = generate_weekly_report(cid, db=db_session)

    assert report["creator_id"] == cid
    assert report["niche"] == "Personal Finance"
    assert "metrics" in report
    assert "trends" in report
    assert "best_posting_window" in report
    assert len(report["content_schedule"]) == 1
    assert len(report["experiments"]) == 1

    # Verify Markdown briefing
    md = report["markdown_report"]
    assert "# Weekly Executive Growth Briefing" in md
    assert "Personal Finance" in md
    assert "Index Funds" in md
    assert "Conclusive Winner" in md

    # Verify Styled Standalone HTML
    html = report["html_report"]
    assert "<!DOCTYPE html>" in html
    assert "Weekly Executive Growth Briefing" in html
    assert "Avg Engagement" in html


def test_get_weekly_report_endpoints(client, db_session):
    cid = "api_rep_creator"

    # Non-existent creator returns 404
    resp_404 = client.get(f"/reports/weekly/non_existent_creator_xyz")
    assert resp_404.status_code == 404

    # Seed creator
    creator = Creator(id=cid, niche="Fitness & Wellness")
    db_session.add(creator)
    p = Post(
        post_id="fit_p1",
        creator_id=cid,
        content_type="reel",
        likes_count=600,
        comments_count=30,
        shares_count=90,
        saves_count=120,
        reach=5500,
        impressions=7000,
        engagement_rate=15.2,
        timestamp=utcnow(),
    )
    db_session.add(p)
    db_session.commit()

    # GET /reports/weekly/{creator_id}
    resp = client.get(f"/reports/weekly/{cid}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["creator_id"] == cid
    assert data["niche"] == "Fitness & Wellness"
    assert "markdown_report" in data

    # GET /reports/weekly/{creator_id}/html
    resp_html = client.get(f"/reports/weekly/{cid}/html")
    assert resp_html.status_code == 200
    assert "text/html" in resp_html.headers.get("content-type", "")
    assert "<!DOCTYPE html>" in resp_html.text


def test_single_session_onboarding_pipeline(client, db_session):
    cid = "onboard_test_creator"
    payload = {
        "creator_id": cid,
        "niche": "Tech & AI",
        "raw_data": [
            {
                "post_id": "ob_1",
                "content_type": "reel",
                "likes_count": 800,
                "comments_count": 50,
                "shares_count": 120,
                "saves_count": 200,
                "reach": 8000,
                "impressions": 11000,
                "timestamp": "2026-10-20T18:00:00Z",
            },
            {
                "post_id": "ob_2",
                "content_type": "carousel",
                "likes_count": 450,
                "comments_count": 30,
                "shares_count": 60,
                "saves_count": 90,
                "reach": 4000,
                "impressions": 5500,
                "timestamp": "2026-10-21T19:00:00Z",
            },
            {
                "post_id": "ob_3",
                "content_type": "reel",
                "likes_count": 1200,
                "comments_count": 90,
                "shares_count": 310,
                "saves_count": 450,
                "reach": 15000,
                "impressions": 21000,
                "timestamp": "2026-10-22T20:30:00Z",
            },
        ],
    }

    resp = client.post("/onboarding/initiate", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "onboarding_completed"
    assert data["creator_id"] == cid
    assert data["niche"] == "Tech & AI"
    assert data["posts_ingested"] == 3
    assert data["data_readiness"]["data_ready"] is True
    assert "initial_strategy" in data
    assert "initial_content_plan" in data
    assert "weekly_report_summary" in data
    assert "markdown_report" in data["weekly_report_summary"]


def test_dashboard_ui_routes(client):
    # GET / should return index.html SPA
    resp_root = client.get("/")
    assert resp_root.status_code == 200
    assert "InstaMap" in resp_root.text
    assert "Growth Engine" in resp_root.text

    # GET /dashboard should also serve index.html SPA
    resp_dash = client.get("/dashboard")
    assert resp_dash.status_code == 200
    assert "Creator Command Center" in resp_dash.text
