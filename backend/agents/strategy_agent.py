"""
backend/agents/strategy_agent.py

Strategy Agent:
Formulates a quantitative-grounded growth strategy for a creator.
Defines content pillars, format distribution (e.g. 60% reels / 30% carousels / 10% images),
target cadence, and strategic priorities.

Supports offline deterministic generation by default, with optional LLM enhancement.
"""

from __future__ import annotations
import json
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from backend.database.models import Creator, Strategy


def _compute_format_allocation(top_content_type: str, breakdown: Dict[str, Any]) -> Dict[str, int]:
    """Computes format distribution percentages based on performance breakdown."""
    normalized_top = (top_content_type or "reel").lower()

    if normalized_top == "reel":
        return {"reel": 60, "carousel": 30, "image": 10}
    elif normalized_top == "carousel":
        return {"carousel": 55, "reel": 35, "image": 10}
    elif normalized_top == "image":
        return {"image": 45, "carousel": 35, "reel": 20}
    else:
        return {"reel": 50, "carousel": 35, "image": 15}


def _determine_pillars(niche: Optional[str] = None) -> List[str]:
    """Generates 3-4 content pillars customized to creator niche."""
    clean_niche = (niche or "general creator").strip().title()
    return [
        f"{clean_niche} Mastery: High-value tactical breakdowns and step-by-step guides",
        f"Authority & Proof: Case studies, experiments, and benchmark analysis",
        f"Behind the Scenes: Unfiltered process, studio workflow, and creator journey",
        f"Perspective & Trends: Hot takes on industry shifts and algorithmic changes",
    ]


def _enhance_strategy_with_llm(
    creator_id: str,
    top_content_type: str,
    avg_er: float,
    recent_trend: str,
    niche: Optional[str],
) -> Optional[Dict[str, Any]]:
    """Optional LLM enhancement for strategy customization."""
    try:
        from backend.agents.llm_client import LLMClient
        client = LLMClient()
        prompt = f"""
You are the Chief Instagram Growth Strategist.
Create a strategic blueprint for creator '{creator_id}' with the following data:
- Primary format: {top_content_type}
- Average Engagement Rate: {avg_er:.2f}%
- Recent Trend: {recent_trend}
- Niche: {niche or 'Creator / Entrepreneurship'}

Return valid JSON with keys:
- "core_pillars": list of 4 descriptive content pillars
- "tone_of_voice": 1-2 sentence description of voice
- "strategic_priorities": list of 3 high-impact tactical priorities
"""
        raw = client.generate(prompt=prompt, system_prompt="You are an expert Instagram strategist. Return valid JSON only.")
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:].strip()
        return json.loads(clean)
    except Exception:
        return None


def run_strategy_agent(
    creator_id: str,
    metrics: Dict[str, Any],
    trends: Dict[str, Any],
    niche: Optional[str] = None,
    audience: Optional[str] = None,
    use_llm: bool = False,
    db: Optional[Session] = None,
) -> Dict[str, Any]:
    """
    Formulates a comprehensive growth strategy for a creator.
    Persists to the Strategy table if db session is provided.
    """
    top_type = metrics.get("top_content_type", "reel")
    avg_er = metrics.get("average_engagement_rate", 0.0)
    recent_trend = trends.get("recent_trend", "stable")
    breakdown = metrics.get("content_type_breakdown", {})

    format_alloc = _compute_format_allocation(top_type, breakdown)
    pillars = _determine_pillars(niche)

    cadence = "4 posts/week"
    if avg_er >= 4.0:
        cadence = "4-5 posts/week"
    elif avg_er < 2.0:
        cadence = "3 posts/week"

    tone = f"Authoritative, high-clarity, and actionable for ambitious {niche or 'professionals'}."
    priorities = [
        f"Scale production of high-performing '{top_type}s' to drive 60% of weekly impressions.",
        "Refine hook retention: test 3 distinct hook angles for every concept in the first 3 seconds.",
        "Include explicit save/share prompts in carousels and reels to trigger viral distribution signals.",
    ]

    # Optional LLM customization
    if use_llm:
        llm_data = _enhance_strategy_with_llm(creator_id, top_type, avg_er, recent_trend, niche)
        if llm_data:
            pillars = llm_data.get("core_pillars", pillars)
            tone = llm_data.get("tone_of_voice", tone)
            priorities = llm_data.get("strategic_priorities", priorities)

    strategy_id = str(uuid.uuid4())
    result = {
        "strategy_id": strategy_id,
        "creator_id": creator_id,
        "primary_content_type": top_type,
        "format_allocation": format_alloc,
        "core_pillars": pillars,
        "target_cadence": cadence,
        "target_audience": audience or f"Aspiring builders and audience in {niche or 'creative growth'}",
        "tone_of_voice": tone,
        "strategic_priorities": priorities,
    }

    if db is not None:
        record = Strategy(
            id=strategy_id,
            creator_id=creator_id,
            primary_content_type=top_type,
            format_allocation=format_alloc,
            core_pillars=pillars,
            target_cadence=cadence,
            target_audience=result["target_audience"],
            tone_of_voice=tone,
            strategic_priorities=priorities,
        )
        db.add(record)
        db.commit()

    return result
