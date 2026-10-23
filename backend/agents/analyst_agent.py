"""
backend/agents/analyst_agent.py

Performance Analyst Agent.
Translates computed post metrics, trend detections, and anomalies into
actionable growth recommendations and executive summaries.

Runs fully offline by default using deterministic rule-based analysis.
LLM enhancement is opt-in via use_llm=True — no external API is ever
called unless explicitly requested.
"""

from __future__ import annotations
import json
from typing import Any, Dict, List, Optional


def _generate_recommendation(
    top_content_type: str,
    recent_trend: str,
    best_posting_window: str,
    anomalies: List[Dict[str, Any]],
    avg_er: float,
    content_breakdown: Dict[str, Any],
) -> str:
    """Deterministic, rule-based recommendation. No external API needed."""
    actions = []

    # Content type guidance
    if top_content_type and top_content_type != "unknown":
        actions.append(f"Double down on {top_content_type}s, which are currently driving your highest engagement.")

    # Posting window guidance
    if best_posting_window and "Insufficient" not in best_posting_window:
        actions.append(f"Schedule high-value posts during your peak window ({best_posting_window}).")

    # Trend-based guidance
    if recent_trend == "declining":
        actions.append("Test new hook formats or adjust content pacing to reverse the recent engagement decline.")
    elif recent_trend == "improving":
        actions.append("Maintain current publishing frequency to capitalize on positive algorithmic momentum.")
    elif recent_trend == "stable":
        actions.append("Experiment with a new content format to break through the current plateau.")

    # Anomaly-based guidance
    if anomalies:
        spikes = [a for a in anomalies if a.get("type") == "spike"]
        drops = [a for a in anomalies if a.get("type") == "drop"]
        if spikes:
            actions.append("Analyze top outlier posts to identify reproducible creative patterns and hooks.")
        if drops:
            actions.append("Review underperforming posts for timing, hook, or format issues.")

    # Engagement rate thresholds
    if avg_er < 1.0:
        actions.append("Focus on improving hooks and calls-to-action — engagement rate is below the 1% baseline.")
    elif avg_er > 5.0:
        actions.append("Engagement rate is strong. Consider increasing posting frequency to maximize reach.")

    # Content diversification check
    if content_breakdown and len(content_breakdown) == 1:
        actions.append("Diversify content formats — relying on a single type limits algorithmic reach.")

    return " ".join(actions) if actions else "Continue regular posting schedule and gather more data."


def _generate_summary(
    creator_id: str,
    avg_er: float,
    top_content_type: str,
    recent_trend: str,
    wow_delta: float,
    total_posts: int,
    anomalies: List[Dict[str, Any]],
) -> str:
    """Deterministic analysis summary. No external API needed."""
    parts = [
        f"Creator {creator_id} has an average engagement rate of {avg_er:.2f}% across {total_posts} posts.",
        f"The top-performing format is {top_content_type}.",
        f"Performance is currently {recent_trend} ({wow_delta:+.1f}% week-over-week).",
    ]

    spike_count = sum(1 for a in anomalies if a.get("type") == "spike")
    drop_count = sum(1 for a in anomalies if a.get("type") == "drop")
    if spike_count or drop_count:
        parts.append(f"Detected {spike_count} spike(s) and {drop_count} drop(s) in recent performance.")

    return " ".join(parts)


def _enhance_with_llm(
    creator_id: str,
    metrics: Dict[str, Any],
    trends: Dict[str, Any],
    best_posting_window: str,
    anomalies: List[Dict[str, Any]],
) -> Dict[str, str]:
    """
    Optional LLM enhancement. Only called when use_llm=True.
    Returns dict with 'recommended_action' and 'analysis_summary' keys,
    or empty dict if LLM call fails.
    """
    try:
        from backend.agents.llm_client import LLMClient
        client = LLMClient()

        avg_er = metrics.get("average_engagement_rate", 0.0)
        top_content_type = metrics.get("top_content_type", "unknown")
        recent_trend = trends.get("recent_trend", "stable")
        wow_delta = trends.get("week_over_week_delta_pct", 0.0)

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
        clean_text = response_text.strip()
        if clean_text.startswith("```"):
            clean_text = clean_text.split("```")[1]
            if clean_text.startswith("json"):
                clean_text = clean_text[4:].strip()
        return json.loads(clean_text)
    except Exception:
        return {}


def run_analyst_agent(
    creator_id: str,
    metrics: Dict[str, Any],
    trends: Dict[str, Any],
    best_posting_window: str,
    anomalies: List[Dict[str, Any]],
    use_llm: bool = False,
    llm_client: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Executes the Performance Analyst Agent.

    Runs fully offline with deterministic rule-based analysis by default.
    Set use_llm=True to optionally enhance with an LLM call (requires
    GROQ_API_KEY or ANTHROPIC_API_KEY in .env).
    """
    top_content_type = metrics.get("top_content_type", "unknown")
    avg_er = metrics.get("average_engagement_rate", 0.0)
    total_posts = metrics.get("total_posts", 0)
    recent_trend = trends.get("recent_trend", "stable")
    wow_delta = trends.get("week_over_week_delta_pct", 0.0)
    content_breakdown = metrics.get("content_type_breakdown", {})

    # Rule-based analysis (always runs, no API needed)
    recommended_action = _generate_recommendation(
        top_content_type, recent_trend, best_posting_window,
        anomalies, avg_er, content_breakdown,
    )
    analysis_summary = _generate_summary(
        creator_id, avg_er, top_content_type, recent_trend,
        wow_delta, total_posts, anomalies,
    )

    # Optional LLM enhancement — only if explicitly requested
    if use_llm:
        llm_result = _enhance_with_llm(
            creator_id, metrics, trends, best_posting_window, anomalies
        )
        if "recommended_action" in llm_result:
            recommended_action = llm_result["recommended_action"]
        if "analysis_summary" in llm_result:
            analysis_summary = llm_result["analysis_summary"]

    return {
        "creator_id": creator_id,
        "top_content_type": top_content_type,
        "average_engagement_rate": avg_er,
        "best_posting_window": best_posting_window,
        "recent_trend": recent_trend,
        "week_over_week_delta_pct": wow_delta,
        "recommended_action": recommended_action,
        "analysis_summary": analysis_summary,
        "content_type_breakdown": content_breakdown,
        "anomalies": anomalies,
        "top_performing_posts": metrics.get("top_performing_posts", []),
        "analysis_mode": "llm_enhanced" if use_llm else "rule_based",
    }
