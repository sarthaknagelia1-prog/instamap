"""
backend/agents/experiment_agent.py

Experiment Agent:
Identifies algorithmic and creative opportunities from creator performance intelligence
to propose high-impact, structured A/B hypothesis tests.
"""

from __future__ import annotations
import json
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from backend.database.models import Experiment


def _propose_deterministic_experiment(
    top_format: str,
    avg_er: float,
    best_window: str,
    niche: Optional[str],
) -> Dict[str, Any]:
    """Generates structured experiment templates based on format and performance."""
    clean_niche = (niche or "creator").strip()

    # If primary format is video/reels, test hook retention
    if top_format == "reel":
        return {
            "title": f"Reel Hook Retention: Contrarian Myth vs Direct How-To",
            "hypothesis": (
                f"Starting Reels with a contrarian provocation will halt scrollers faster than direct how-to hooks, "
                f"increasing average engagement rate by at least +15%."
            ),
            "metric_target": "engagement_rate",
            "controlled_variables": {
                "content_type": "reel",
                "video_length": "30-45 seconds",
                "posting_window": best_window,
                "niche": clean_niche,
            },
            "variant_a": {
                "name": "Direct How-To Hook",
                "description": "Directly announce the tip in the first 2 seconds (e.g. 'Here is how to...')",
                "post_ids": [],
            },
            "variant_b": {
                "name": "Contrarian Myth Hook",
                "description": "Provoke scrollers by challenging accepted wisdom (e.g. 'Stop doing X if you want Y...')",
                "post_ids": [],
            },
            "instructions": [
                "Post 3 Reels using Variant A (Direct How-To) and 3 Reels using Variant B (Contrarian Myth) over 2 weeks.",
                "Keep topic difficulty, video length (30-45s), and posting time identical.",
                "Re-upload your metrics to evaluate statistical significance.",
            ],
        }
    elif top_format == "carousel":
        return {
            "title": f"Carousel Value Delivery: Framework Flowchart vs Checklist",
            "hypothesis": (
                f"Visual flowchart comparisons will drive higher saves and shares than text-based checklists, "
                f"increasing save-to-reach ratio."
            ),
            "metric_target": "engagement_rate",
            "controlled_variables": {
                "content_type": "carousel",
                "slide_count": "6-8 slides",
                "niche": clean_niche,
            },
            "variant_a": {
                "name": "Text Checklist Format",
                "description": "Step-by-step bulleted actionable checklist per slide",
                "post_ids": [],
            },
            "variant_b": {
                "name": "Visual Flowchart Format",
                "description": "High-contrast visual diagrams and before-after comparison graphics",
                "post_ids": [],
            },
            "instructions": [
                "Publish 3 Carousels using Variant A and 3 Carousels using Variant B.",
                "Compare engagement and save rates upon completion.",
            ],
        }
    else:  # Scheduling test
        return {
            "title": f"Publishing Timing Test: Peak Evening vs Lunchtime Window",
            "hypothesis": (
                f"Publishing during peak algorithmic evening hours ({best_window}) will yield at least 20% more initial reach "
                f"compared to midday posting."
            ),
            "metric_target": "reach",
            "controlled_variables": {
                "content_type": top_format,
                "niche": clean_niche,
            },
            "variant_a": {
                "name": "Midday Posting Window (12:00 - 13:30 UTC)",
                "description": "Post during lunchtime break",
                "post_ids": [],
            },
            "variant_b": {
                "name": f"Peak Evening Window ({best_window})",
                "description": "Post during verified peak activity slot",
                "post_ids": [],
            },
            "instructions": [
                "Publish 3 posts at 12:30 UTC and 3 posts during the peak evening window.",
                "Evaluate reach and impressions delta.",
            ],
        }


def _enhance_experiment_with_llm(
    top_format: str,
    avg_er: float,
    niche: Optional[str],
) -> Optional[Dict[str, Any]]:
    """Optional LLM enhancement for custom hypothesis formulation."""
    try:
        from backend.agents.llm_client import LLMClient
        client = LLMClient()
        prompt = f"""
You are an expert Social Media Experimentation Scientist.
Design a high-impact A/B experiment for an Instagram creator:
- Format: {top_format}
- Average Engagement Rate: {avg_er:.2f}%
- Niche: {niche or 'Creator'}

Return valid JSON with keys:
- "title": experiment title
- "hypothesis": testable hypothesis with expected % lift
- "metric_target": primary metric ("engagement_rate" or "reach")
- "controlled_variables": dict of controlled factors
- "variant_a": dict with "name", "description", "post_ids": []
- "variant_b": dict with "name", "description", "post_ids": []
- "instructions": list of 3 creator execution steps
"""
        raw = client.generate(prompt=prompt, system_prompt="You are a data-driven experimentation scientist. Return valid JSON only.")
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:].strip()
        return json.loads(clean)
    except Exception:
        return None


def run_experiment_agent(
    creator_id: str,
    metrics: Optional[Dict[str, Any]] = None,
    trends: Optional[Dict[str, Any]] = None,
    niche: Optional[str] = None,
    use_llm: bool = False,
    db: Optional[Session] = None,
    top_format: Optional[str] = None,
    avg_er: Optional[float] = None,
    best_window: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Formulates a statistically testable hypothesis and creates an Experiment record.
    """
    metrics_dict = metrics or {}
    trends_dict = trends or {}

    actual_format = top_format or metrics_dict.get("top_content_type", "reel")
    actual_avg_er = avg_er if avg_er is not None else metrics_dict.get("average_engagement_rate", 0.0)
    actual_window = best_window or trends_dict.get("best_posting_window", "18:00 - 21:00 UTC")

    experiment_data = _propose_deterministic_experiment(actual_format, actual_avg_er, actual_window, niche)

    if use_llm:
        llm_exp = _enhance_experiment_with_llm(top_format, avg_er, niche)
        if llm_exp:
            experiment_data = {**experiment_data, **llm_exp}

    exp_id = str(uuid.uuid4())
    result = {
        "id": exp_id,
        "creator_id": creator_id,
        "title": experiment_data["title"],
        "hypothesis": experiment_data["hypothesis"],
        "metric_target": experiment_data.get("metric_target", "engagement_rate"),
        "status": "proposed",
        "controlled_variables": experiment_data.get("controlled_variables", {}),
        "variant_a": experiment_data.get("variant_a", {}),
        "variant_b": experiment_data.get("variant_b", {}),
        "instructions": experiment_data.get("instructions", []),
        "evaluation_result": {},
    }

    if db is not None:
        record = Experiment(
            id=exp_id,
            creator_id=creator_id,
            title=result["title"],
            hypothesis=result["hypothesis"],
            metric_target=result["metric_target"],
            status="proposed",
            controlled_variables=result["controlled_variables"],
            variant_a=result["variant_a"],
            variant_b=result["variant_b"],
            evaluation_result={},
        )
        db.add(record)
        db.commit()

    return result
