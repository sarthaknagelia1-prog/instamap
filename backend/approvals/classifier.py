"""
backend/approvals/classifier.py

Action Classifier:
Evaluates agent actions to determine whether they can be auto-approved
(reports, data readiness, passive intelligence) or require human-in-the-loop
creator review (content drafts, strategic pivots, A/B experiments).
"""

from __future__ import annotations
from typing import Any, Dict


AUTO_APPROVED_ACTIONS = {
    "analyze_performance",
    "report_only",
    "request_more_data",
    "sniff_trends",
    "data_readiness_check",
    "health_check",
}

REVIEW_REQUIRED_ACTIONS = {
    "draft_approval": {
        "risk_level": "high",
        "reasoning": "Direct public-facing creative copy, hashtags, and media instructions.",
    },
    "strategy_pivot": {
        "risk_level": "medium",
        "reasoning": "Modifies core creator pillars, cadence, and format bandwidth allocations.",
    },
    "content_plan_approval": {
        "risk_level": "medium",
        "reasoning": "Schedules a 7-day weekly posting calendar.",
    },
    "experiment_launch": {
        "risk_level": "medium",
        "reasoning": "Launches a controlled hypothesis test altering content variables.",
    },
}


def classify_action(action_type: str, item_type: str = "generic", payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Classifies an action as auto-approved or review-required with risk assessment.
    """
    clean_action = (action_type or "").lower().strip()

    if clean_action in AUTO_APPROVED_ACTIONS:
        return {
            "requires_review": False,
            "auto_approve": True,
            "risk_level": "low",
            "reasoning": "Passive diagnostic, read-only analysis, or algorithmic data assessment.",
        }

    config = REVIEW_REQUIRED_ACTIONS.get(clean_action)
    if config:
        return {
            "requires_review": True,
            "auto_approve": False,
            "risk_level": config["risk_level"],
            "reasoning": config["reasoning"],
        }

    # Item type fallback heuristics
    clean_item = (item_type or "").lower().strip()
    if clean_item in ("content_draft", "draft"):
        return {
            "requires_review": True,
            "auto_approve": False,
            "risk_level": "high",
            "reasoning": "Content draft requires human creator approval before manual publishing.",
        }
    elif clean_item in ("strategy", "content_plan", "experiment"):
        return {
            "requires_review": True,
            "auto_approve": False,
            "risk_level": "medium",
            "reasoning": f"Modifications to {clean_item} require creator review.",
        }

    # Default safe: review required if uncertain
    return {
        "requires_review": True,
        "auto_approve": False,
        "risk_level": "medium",
        "reasoning": f"Unrecognized action '{action_type}' defaults to review-required for safety.",
    }
