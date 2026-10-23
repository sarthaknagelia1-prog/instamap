"""
backend/agents/content_planning_agent.py

Content Planning Agent:
Converts creator strategy and peak posting window intelligence into a
structured, day-by-day 7-day content calendar.
"""

from __future__ import annotations
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from backend.database.models import ContentPlan


def run_content_planning_agent(
    creator_id: str,
    strategy: Dict[str, Any],
    best_posting_window: Optional[str] = None,
    week_number: int = 1,
    trending_topics: Optional[List[Dict[str, Any]]] = None,
    db: Optional[Session] = None,
) -> Dict[str, Any]:
    """
    Generates a 7-day content schedule matching creator strategy and peak posting windows.
    """
    primary_format = strategy.get("primary_content_type", "reel")
    pillars = strategy.get("core_pillars", ["Educational Guide", "Authority Proof", "Behind the Scenes", "Trends"])
    window = best_posting_window if best_posting_window and "Insufficient" not in best_posting_window else "18:00 - 20:00 UTC"

    p1 = pillars[0] if len(pillars) > 0 else "Educational breakdown"
    p2 = pillars[1] if len(pillars) > 1 else "Authority proof"
    p3 = pillars[2] if len(pillars) > 2 else "Behind the scenes"
    p4 = pillars[3] if len(pillars) > 3 else "Trend commentary"

    scheduled_items = [
        {
            "day": "Monday",
            "content_type": primary_format,
            "theme": p1,
            "concept_angle": "Actionable step-by-step breakdown solving the #1 pain point",
            "scheduled_time": f"Monday {window.split()[-2] if ' ' in window else '18:30'} UTC",
            "target_metric": "Saves & Shares",
        },
        {
            "day": "Tuesday",
            "content_type": "story",
            "theme": "Community Engagement",
            "concept_angle": "Interactive poll + Q&A sticker related to Monday's post",
            "scheduled_time": "Tuesday 12:00 UTC",
            "target_metric": "Direct Messages & Replies",
        },
        {
            "day": "Wednesday",
            "content_type": "carousel" if primary_format != "carousel" else "reel",
            "theme": p2,
            "concept_angle": "Data-backed case study, framework, or transformation breakdown",
            "scheduled_time": "Wednesday 18:30 UTC",
            "target_metric": "Saves & Profile Visits",
        },
        {
            "day": "Friday",
            "content_type": (trending_topics[0].get("recommended_format") if trending_topics else primary_format),
            "theme": p4,
            "concept_angle": (trending_topics[0]["suggested_angle"] if trending_topics else "Strong contrarian hook debunking a common myth in your niche"),
            "hook_preview": (trending_topics[0]["suggested_hook"] if trending_topics else None),
            "trending_topic": (trending_topics[0]["topic"] if trending_topics else None),
            "scheduled_time": f"Friday {window.split()[-2] if ' ' in window else '19:00'} UTC",
            "target_metric": "Reach & Viral Discovery",
        },
        {
            "day": "Sunday",
            "content_type": "image" if primary_format != "image" else "carousel",
            "theme": p3,
            "concept_angle": "High-authenticity behind-the-scenes reflection / personal lesson",
            "scheduled_time": "Sunday 17:00 UTC",
            "target_metric": "Comments & Connection",
        },
    ]

    plan_id = str(uuid.uuid4())
    result = {
        "plan_id": plan_id,
        "creator_id": creator_id,
        "strategy_id": strategy.get("strategy_id"),
        "week_number": week_number,
        "planned_post_count": len([item for item in scheduled_items if item["content_type"] != "story"]),
        "scheduled_items": scheduled_items,
    }

    if db is not None:
        record = ContentPlan(
            id=plan_id,
            creator_id=creator_id,
            strategy_id=strategy.get("strategy_id"),
            week_number=week_number,
            scheduled_items=scheduled_items,
        )
        db.add(record)
        db.commit()

    return result
