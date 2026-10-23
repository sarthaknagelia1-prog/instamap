"""
backend/orchestrator/decision_engine.py

Deterministic decision engine evaluating creator performance metrics
against configurable rules and thresholds to choose the optimal agent path.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional

from backend.agents.schemas import DecisionThresholds, OrchestratorAction, OrchestratorDecision


def evaluate_decision(
    total_posts: int,
    days_since_last_post: Optional[int],
    metrics: Dict[str, Any],
    trends: Dict[str, Any],
    anomalies: List[Dict[str, Any]],
    thresholds: Optional[DecisionThresholds] = None,
) -> OrchestratorDecision:
    """
    Evaluates creator context against decision rules and returns a structured decision.
    """
    th = thresholds or DecisionThresholds()
    reasons: List[str] = []

    # Rule 1: Insufficient posts
    if total_posts < th.min_posts_required:
        reason = f"Only {total_posts} post(s) found. Minimum {th.min_posts_required} required to establish statistical baseline."
        return OrchestratorDecision(
            action=OrchestratorAction.REQUEST_MORE_DATA,
            primary_reason=reason,
            reasons=[reason],
            suggested_focus="Ingest more historical posts",
            confidence_score=1.0,
        )

    # Rule 2: Stale data
    if days_since_last_post is not None and days_since_last_post > th.max_staleness_days:
        reason = f"Latest post was {days_since_last_post} days ago, exceeding the {th.max_staleness_days}-day staleness threshold."
        return OrchestratorDecision(
            action=OrchestratorAction.REQUEST_MORE_DATA,
            primary_reason=reason,
            reasons=[reason],
            suggested_focus="Upload recent post performance data",
            confidence_score=0.95,
        )

    # Rule 3: Significant drop or negative trend
    wow_delta = trends.get("week_over_week_delta_pct", 0.0)
    recent_trend = trends.get("recent_trend", "stable")
    avg_er = metrics.get("average_engagement_rate", 0.0)

    drops = [a for a in anomalies if a.get("type") == "drop"]
    has_severe_drop = any(abs(a.get("deviation_pct", 0)) >= abs(th.severe_drop_threshold_pct) for a in drops)

    if wow_delta <= th.engagement_drop_threshold_pct:
        reasons.append(f"Week-over-week engagement fell by {abs(wow_delta):.1f}% (threshold: {abs(th.engagement_drop_threshold_pct):.1f}%).")
    if recent_trend == "declining":
        reasons.append("Overall engagement trend is currently classified as declining.")
    if has_severe_drop:
        reasons.append(f"Severe negative anomaly detected exceeding {abs(th.severe_drop_threshold_pct)}% drop.")

    if reasons:
        return OrchestratorDecision(
            action=OrchestratorAction.GENERATE_FULL_PLAN,
            primary_reason=reasons[0],
            reasons=reasons,
            suggested_focus="Creative format pivot, hook optimization, and posting schedule adjustment",
            confidence_score=0.9,
        )

    # Rule 4: Sub-baseline engagement rate
    if avg_er < th.low_engagement_threshold:
        reason = f"Average engagement rate ({avg_er:.2f}%) is below the healthy baseline of {th.low_engagement_threshold}%."
        return OrchestratorDecision(
            action=OrchestratorAction.GENERATE_STRATEGY_ONLY,
            primary_reason=reason,
            reasons=[reason],
            suggested_focus="Content type diversification and audience hook alignment",
            confidence_score=0.85,
        )

    # Rule 5: Healthy / improving performance
    reason = f"Performance is {recent_trend} ({wow_delta:+.1f}% WoW) with {avg_er:.2f}% average engagement rate."
    return OrchestratorDecision(
        action=OrchestratorAction.REPORT_ONLY,
        primary_reason=reason,
        reasons=[reason, "Maintain current content cadence and monitor upcoming post performance."],
        suggested_focus="Double down on top-performing format and preserve posting cadence",
        confidence_score=0.95,
    )
