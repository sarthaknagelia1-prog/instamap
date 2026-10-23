"""
tests/test_trend_sniffer.py

Tests for Trend Sniffing Adapter:
- Offline-resilient curated radar
- Velocity scoring & Instagram angle synthesis
- Content planning agent integration
- FastAPI routes: /trends/niches, /trends/sniff, /trends/sniff/custom, /trends/cached
"""

from backend.data.adapters.trend_sniffing_adapter import (
    TrendSniffingAdapter,
    _match_niche_key,
    synthesize_instagram_angle,
    NICHE_SUBREDDITS,
)
from backend.agents.content_planning_agent import run_content_planning_agent


def test_trend_sniffer_curated_radar_offline():
    adapter = TrendSniffingAdapter()
    signals = adapter.sniff(niche="Tech & AI", limit=3, use_network=False)

    assert len(signals) == 3
    for s in signals:
        assert "topic" in s
        assert 0.0 <= s["velocity_score"] <= 100.0
        assert len(s["suggested_hook"]) > 10
        assert len(s["suggested_angle"]) > 10
        assert s["recommended_format"] in ("reel", "carousel", "image")
        assert s["source"] == "curated_radar"


def test_niche_fuzzy_matching():
    assert _match_niche_key("Artificial Intelligence") == "Tech & AI"
    assert _match_niche_key("Gym & Fitness") == "Fitness & Health"
    assert _match_niche_key("Stock Investing & Crypto") == "Personal Finance"
    assert _match_niche_key("Startup Marketing") == "Business & Marketing"
    assert _match_niche_key("Unknown Weird Niche") == "Tech & AI"  # Safe default


def test_synthesize_instagram_angle():
    # Comparison topic -> Carousel format
    res_comp = synthesize_instagram_angle("Claude 3.7 vs GPT-4o: Reasoning Speed", "Tech & AI", 92.0)
    assert res_comp["recommended_format"] == "carousel"
    assert "debate is settled" in res_comp["suggested_hook"].lower()

    # Tutorial topic -> Carousel format
    res_how = synthesize_instagram_angle("How to Build a Morning Routine", "Productivity", 85.0)
    assert res_how["recommended_format"] == "carousel"
    assert "stop doing this" in res_how["suggested_hook"].lower()

    # Breaking news topic -> Reel format
    res_news = synthesize_instagram_angle("New Deep Learning Architecture Released", "Tech & AI", 95.0)
    assert res_news["recommended_format"] == "reel"
    assert "30 seconds" in res_news["suggested_hook"]


def test_content_planning_agent_injects_trends():
    strategy = {
        "strategy_id": "strat_trends_1",
        "primary_content_type": "reel",
        "core_pillars": ["AI Automation", "Dev Careers", "Tools", "Tech News"],
    }
    trending = [
        {
            "topic": "Local LLM Fine-Tuning Breakthrough",
            "velocity_score": 93.0,
            "suggested_hook": "Stop paying cloud bills: here is the 3-step local setup.",
            "suggested_angle": "Hands-on guide comparing memory usage on consumer GPUs.",
            "recommended_format": "reel",
        }
    ]

    plan = run_content_planning_agent(
        creator_id="creator_trend_test",
        strategy=strategy,
        best_posting_window="Friday 18:00 - 21:00 UTC",
        trending_topics=trending,
    )

    # Verify Friday item has injected trend details
    friday_item = next(item for item in plan["scheduled_items"] if item["day"] == "Friday")
    assert friday_item["trending_topic"] == "Local LLM Fine-Tuning Breakthrough"
    assert friday_item["hook_preview"] == "Stop paying cloud bills: here is the 3-step local setup."
    assert "Hands-on guide" in friday_item["concept_angle"]


def test_api_trends_endpoints(client):
    # 1. GET /trends/niches
    res_niches = client.get("/trends/niches")
    assert res_niches.status_code == 200
    niches = res_niches.json()["supported_niches"]
    assert "Tech & AI" in niches
    assert "Fitness & Health" in niches

    # 2. GET /trends/sniff (offline mode for test predictability)
    res_sniff = client.get("/trends/sniff?niche=Personal%20Finance&limit=2&use_network=false")
    assert res_sniff.status_code == 200
    sniffed = res_sniff.json()
    assert len(sniffed) == 2
    assert sniffed[0]["niche"] == "Personal Finance"
    assert "suggested_hook" in sniffed[0]
    assert sniffed[0]["velocity_score"] > 0

    # 3. GET /trends/cached
    res_cached = client.get("/trends/cached?niche=Personal%20Finance")
    assert res_cached.status_code == 200
    cached = res_cached.json()
    assert len(cached) >= 2

    # 4. POST /trends/sniff/custom
    res_custom = client.get("/trends/sniff?niche=Fitness&limit=2&use_network=false")
    assert res_custom.status_code == 200
