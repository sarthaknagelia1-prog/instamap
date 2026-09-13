"""
backend/agents/analyst_agent.py

Performance Analyst Agent.
Translates computed post metrics, trend detections, and anomalies into
actionable growth recommendations and executive summaries.
"""

from __future__ import annotations
import json
from typing import Any, Dict, List, Optional

from backend.agents.llm_client import LLMClient


def _generate_fallback_recommendation(
    top_content_type: str,
    recent_trend: str,
    best_posting_window: str,
    anomalies: List[Dict[str, Any]],
) -> str:
    """Deterministic, rule-based recommendation if LLM is offline or unconfigured."""
    actions = []
    if top_content_type and top_content_type != "unknown":
        actions.append(f"Double down on {top_content_type}s, which are currently driving your highest engagement.")

    if best_posting_window and "Insufficient" not in best_posting_window:
        actions.append(f"Schedule high-value posts during your peak window ({best_posting_window}).")

    if recent_trend == "declining":
        actions.append("Test new hook formats or adjust content pacing to reverse the recent engagement decline.")
    elif recent_trend == "improving":
        actions.append("Maintain current publishing frequency to capitalize on positive algorithmic momentum.")

    if anomalies:
        spikes = [a for a in anomalies if a.get("type") == "spike"]
        if spikes:
            actions.append("Analyze top outlier posts to identify reproducible creative patterns and hooks.")

    return " ".join(actions) if actions else "Continue regular posting schedule and gather more data."


def run_analyst_agent(
    creator_id: str,
    metrics: Dict[str, Any],
    trends: Dict[str, Any],
    best_posting_window: str,
    anomalies: List[Dict[str, Any]],
    llm_client: Optional[LLMClient] = None,
) -> Dict[str, Any]:
    """
    Executes the Performance Analyst Agent.
    Combines quantitative intelligence with LLM reasoning.
    """
    top_content_type = metrics.get("top_content_type", "unknown")
    avg_er = metrics.get("average_engagement_rate", 0.0)
    recent_trend = trends.get("recent_trend", "stable")
    wow_delta = trends.get("week_over_week_delta_pct", 0.0)

    recommended_action = _generate_fallback_recommendation(
        top_content_type, recent_trend, best_posting_window, anomalies
    )
    analysis_summary = (
        f"Creator {creator_id} has an average engagement rate of {avg_er:.2f}%. "
        f"The top-performing format is {top_content_type}. "
        f"Performance is currently {recent_trend} ({wow_delta:+.1f}% WoW)."
    )

    # Attempt LLM generation if client available
    client = llm_client or LLMClient()
    try:
        prompt = f"""
You are the Performance Analyst Agent for an Instagram creator.
Analyze the following performance metrics and generate:
1. A concise, high-impact 'recommended_action' (1-2 actionable sentences).
2. A succinct 'analysis_summary' (2-3 sentences explaining the 'why' behind recent metrics).

Metrics:
- Creator ID: {creator_id}
- Total Posts Analyzed: {metrics.get('total_posts', 0)}
- Average Engagement Rate: {avg_er:.2f}%
- Top Performing Content Type: {top_content_type}
- Best Posting Window: {best_posting_window}
- Recent Trend: {recent_trend} (Week-over-Week delta: {wow_delta:+.1f}%)
- Content Breakdown: {json.dumps(metrics.get('content_type_breakdown', {}))}
- Detected Anomalies: {json.dumps(anomalies)}

Respond strictly in JSON format with keys "recommended_action" and "analysis_summary".
"""
        response_text = client.generate(
            prompt=prompt,
            system_prompt="You are a data-driven Instagram growth strategist. Return valid JSON only.",
        )
        # Parse JSON from response
        clean_text = response_text.strip()
        if clean_text.startswith("```"):
            clean_text = clean_text.split("```")[1]
            if clean_text.startswith("json"):
                clean_text = clean_text[4:].strip()
        parsed = json.loads(clean_text)
        if "recommended_action" in parsed:
            recommended_action = parsed["recommended_action"]
        if "analysis_summary" in parsed:
            analysis_summary = parsed["analysis_summary"]
    except Exception:
        # Fall back gracefully to rule-based recommendation
        pass

    return {
        "creator_id": creator_id,
        "top_content_type": top_content_type,
        "average_engagement_rate": avg_er,
        "best_posting_window": best_posting_window,
        "recent_trend": recent_trend,
        "week_over_week_delta_pct": wow_delta,
        "recommended_action": recommended_action,
        "analysis_summary": analysis_summary,
        "content_type_breakdown": metrics.get("content_type_breakdown", {}),
        "anomalies": anomalies,
        "top_performing_posts": metrics.get("top_performing_posts", []),
    }
