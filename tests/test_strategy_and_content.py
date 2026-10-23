"""
tests/test_strategy_and_content.py

Tests for Phase 4:
- Strategy Agent (format distribution, content pillars)
- Content Planning Agent (7-day calendar)
- Content Generation Agent (hook, body, CTA, hashtags, visual direction)
- Strategy & Content API routes
- Orchestrator integration producing complete strategy + content bundle
"""

from datetime import datetime, timezone, timedelta
from backend.agents.strategy_agent import run_strategy_agent
from backend.agents.content_planning_agent import run_content_planning_agent
from backend.agents.content_generation_agent import run_content_generation_agent


def test_strategy_agent_deterministic():
    metrics = {
        "top_content_type": "reel",
        "average_engagement_rate": 4.5,
        "content_type_breakdown": {"reel": {"average_engagement_rate": 4.8}},
    }
    trends = {"recent_trend": "improving", "week_over_week_delta_pct": 5.0}

    strat = run_strategy_agent(
        creator_id="creator_test_s1",
        metrics=metrics,
        trends=trends,
        niche="Fitness Coaching",
    )

    assert strat["creator_id"] == "creator_test_s1"
    assert strat["primary_content_type"] == "reel"
    assert strat["format_allocation"]["reel"] == 60
    assert strat["format_allocation"]["carousel"] == 30
    assert len(strat["core_pillars"]) >= 3
    assert len(strat["strategic_priorities"]) >= 3
    assert strat["target_cadence"] == "4-5 posts/week"


def test_content_planning_agent():
    strategy = {
        "strategy_id": "strat_123",
        "primary_content_type": "reel",
        "core_pillars": ["Pillar 1", "Pillar 2", "Pillar 3"],
    }
    plan = run_content_planning_agent(
        creator_id="creator_test_p1",
        strategy=strategy,
        best_posting_window="Friday 18:00 - 21:00 UTC",
    )

    assert plan["creator_id"] == "creator_test_p1"
    assert plan["planned_post_count"] >= 3
    assert len(plan["scheduled_items"]) == 5
    # Verify days are scheduled
    days = [item["day"] for item in plan["scheduled_items"]]
    assert "Monday" in days
    assert "Friday" in days


def test_content_generation_agent_reel():
    item = {
        "content_type": "reel",
        "theme": "Video Retention",
        "concept_angle": "How to double watch time",
        "scheduled_time": "Friday 18:30 UTC",
    }
    draft = run_content_generation_agent(
        creator_id="creator_test_d1",
        plan_item=item,
        niche="Tech",
    )

    assert draft["content_type"] == "reel"
    assert len(draft["hook"]) > 10
    assert len(draft["body"]) > 20
    assert "Save" in draft["call_to_action"] or "Share" in draft["call_to_action"]
    assert len(draft["hashtags"]) >= 3
    assert draft["visual_direction"] is not None
    assert draft["status"] == "draft"


def test_strategy_and_content_api_endpoints(client):
    now = datetime.now(timezone.utc)
    # 1. Ingest posts
    payload = {
        "creator_id": "creator_full_phase4",
        "raw_data": [
            {"post_id": f"p4_{i}", "date": (now - timedelta(days=7 - i)).isoformat(), "type": "carousel", "likes": 150, "comments": 15}
            for i in range(5)
        ],
    }
    client.post("/data/ingest", json=payload)

    # 2. POST /strategy/generate
    res_strat = client.post("/strategy/generate", json={"creator_id": "creator_full_phase4", "niche": "Marketing"})
    assert res_strat.status_code == 200
    strat_data = res_strat.json()
    assert strat_data["creator_id"] == "creator_full_phase4"
    assert "strategy_id" in strat_data

    # 3. GET /strategy/{creator_id}
    res_get_strat = client.get("/strategy/creator_full_phase4")
    assert res_get_strat.status_code == 200
    assert res_get_strat.json()["strategy_id"] == strat_data["strategy_id"]

    # 4. POST /content/plan
    res_plan = client.post("/content/plan", json={"creator_id": "creator_full_phase4"})
    assert res_plan.status_code == 200
    plan_data = res_plan.json()
    assert "plan_id" in plan_data
    plan_id = plan_data["plan_id"]

    # 5. POST /content/generate
    res_drafts = client.post("/content/generate", json={"creator_id": "creator_full_phase4", "plan_id": plan_id})
    assert res_drafts.status_code == 200
    drafts = res_drafts.json()
    assert len(drafts) >= 1
    draft_id = drafts[0]["id"]

    # 6. GET /content/drafts
    res_list = client.get("/content/drafts?creator_id=creator_full_phase4")
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1

    # 7. GET /content/drafts/{id}
    res_single = client.get(f"/content/drafts/{draft_id}")
    assert res_single.status_code == 200
    assert res_single.json()["id"] == draft_id

    # 8. PATCH /content/drafts/{id}/status
    res_patch = client.patch(f"/content/drafts/{draft_id}/status", json={"status": "approved"})
    assert res_patch.status_code == 200
    assert res_patch.json()["status"] == "approved"


def test_orchestrator_triggers_full_strategy_and_content_bundle(client):
    now = datetime.now(timezone.utc)
    # Creator with declining engagement triggering GENERATE_FULL_PLAN
    payload = {
        "creator_id": "creator_declining_e2e",
        "raw_data": [
            {"post_id": "dec_1", "date": (now - timedelta(days=12)).isoformat(), "type": "image", "likes": 500, "comments": 50},
            {"post_id": "dec_2", "date": (now - timedelta(days=10)).isoformat(), "type": "image", "likes": 400, "comments": 40},
            {"post_id": "dec_3", "date": (now - timedelta(days=3)).isoformat(), "type": "image", "likes": 100, "comments": 5},
            {"post_id": "dec_4", "date": (now - timedelta(days=1)).isoformat(), "type": "image", "likes": 80, "comments": 4},
        ],
    }
    client.post("/data/ingest", json=payload)

    # Run creator-plan
    plan_res = client.post(
        "/creator-plan",
        json={"creator_id": "creator_declining_e2e", "trigger_event": "manual"},
    )
    assert plan_res.status_code == 200
    data = plan_res.json()

    assert data["decision"]["action"] in ("generate_full_plan", "generate_strategy_only")
    assert data["output"]["status"] == "strategy_and_content_bundle_generated"
    assert "strategy" in data["output"]
    assert "content_plan" in data["output"]
    assert "primary_draft" in data["output"]

    # Verify agent hops in execution trace
    agents_run = [msg["agent_name"] for msg in data["execution_trace"]]
    assert "context_fetcher" in agents_run
    assert "performance_analyst" in agents_run
    assert "decision_engine" in agents_run
    assert "strategy_agent" in agents_run
    assert "content_planning_agent" in agents_run
    assert "content_generation_agent" in agents_run
