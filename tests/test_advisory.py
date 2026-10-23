"""
tests/test_advisory.py

Tests for the AI Growth Advisor (Chatbot Engine):
- Advisory context assembly from PostgreSQL metrics
- Deterministic response generation for hooks, timing, engagement, and content planning
- Suggested followup chip synthesis
- REST API endpoints (POST /advisory/chat, GET /advisory/prompts/{creator_id})
"""

import pytest
from backend.database.models import Creator, Post, Strategy, ContentPlan, utcnow
from backend.agents.advisory_agent import (
    gather_creator_advisory_context,
    run_advisory_agent,
    generate_deterministic_advice,
    get_suggested_followups,
)


def test_advisory_agent_context_gathering(db_session):
    cid = "adv_creator_1"
    creator = Creator(id=cid, niche="Tech & AI")
    db_session.add(creator)

    post = Post(
        post_id="p_adv_1",
        creator_id=cid,
        content_type="reel",
        likes_count=600,
        comments_count=40,
        shares_count=120,
        saves_count=160,
        reach=6000,
        impressions=8000,
        engagement_rate=15.3,
        timestamp=utcnow(),
    )
    db_session.add(post)
    db_session.commit()

    ctx = gather_creator_advisory_context(cid, db=db_session)
    assert ctx["creator_id"] == cid
    assert ctx["niche"] == "Tech & AI"
    assert ctx["total_posts"] == 1
    assert ctx["average_engagement_rate"] > 0
    assert "best_posting_window" in ctx
    assert "trending_topics" in ctx


def test_advisory_agent_deterministic_intents():
    ctx = {
        "creator_id": "test_guru",
        "niche": "Fitness & Wellness",
        "average_engagement_rate": 8.08,
        "total_reach": 64000,
        "top_content_type": "reel",
        "best_posting_window": "Friday 18:00 - 21:00 UTC",
        "week_over_week_delta": 9.3,
        "recent_trend": "improving",
        "trending_topics": ["Calisthenics Workouts", "Creatine Timing"],
    }

    # 1. Engagement intent
    rep_eng = generate_deterministic_advice("Why is my engagement rate at 8%?", ctx)
    assert "8.08%" in rep_eng
    assert "Performance Analysis" in rep_eng

    # 2. Timing intent
    rep_time = generate_deterministic_advice("When is the best time to post my reel?", ctx)
    assert "Friday 18:00 - 21:00 UTC" in rep_time
    assert "60-Minute Velocity Window" in rep_time

    # 3. Hooks intent
    rep_hook = generate_deterministic_advice("Give me viral hooks for my video", ctx)
    assert "3 High-Retention Hooks" in rep_hook
    assert "Loss Aversion" in rep_hook

    # 4. What to post intent
    rep_plan = generate_deterministic_advice("What should I post this week?", ctx)
    assert "Action Blueprint" in rep_plan
    assert "Educational Reel" in rep_plan


def test_advisory_followup_suggestions():
    ctx = {"niche": "Tech & AI"}
    f_hooks = get_suggested_followups("Tell me hooks", ctx)
    assert len(f_hooks) == 3

    f_time = get_suggested_followups("When to post?", ctx)
    assert len(f_time) == 3


def test_api_advisory_chat_and_prompts(client, db_session):
    cid = "api_adv_creator"
    creator = Creator(id=cid, niche="Personal Finance")
    db_session.add(creator)
    db_session.commit()

    # GET /advisory/prompts/{creator_id}
    p_res = client.get(f"/advisory/prompts/{cid}")
    assert p_res.status_code == 200
    p_data = p_res.json()
    assert len(p_data["starter_prompts"]) >= 3
    assert "Personal Finance" in p_data["starter_prompts"][0]

    # POST /advisory/chat (Success)
    chat_payload = {
        "creator_id": cid,
        "message": "How do I increase my reel reach and saves?",
    }
    c_res = client.post("/advisory/chat", json=chat_payload)
    assert c_res.status_code == 200
    c_data = c_res.json()
    assert "reply" in c_data
    assert len(c_data["suggested_followups"]) == 3
    assert "grounded_context" in c_data

    # POST /advisory/chat (Validation empty message)
    bad_res = client.post("/advisory/chat", json={"creator_id": cid, "message": "   "})
    assert bad_res.status_code == 400
