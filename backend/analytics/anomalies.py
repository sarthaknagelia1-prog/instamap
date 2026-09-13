"""
backend/analytics/anomalies.py

Anomaly detection to flag sudden engagement spikes and drops
relative to a creator's historical baseline.
"""

from __future__ import annotations
import math
from typing import Any, Dict, List
from backend.analytics.metrics import calculate_post_engagement_rate


def detect_anomalies(posts: List[Dict[str, Any]], z_threshold: float = 1.75) -> List[Dict[str, Any]]:
    """
    Flags posts that significantly deviate (spikes or drops) from the creator's
    engagement rate baseline.
    """
    valid_posts = []
    for p in posts:
        er = p.get("engagement_rate")
        if er is None:
            er = calculate_post_engagement_rate(p)
        if er is not None:
            valid_posts.append({**p, "er": er})

    if len(valid_posts) < 3:
        return []

    values = [p["er"] for p in valid_posts]
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    std_dev = math.sqrt(variance)

    anomalies: List[Dict[str, Any]] = []

    for p in valid_posts:
        val = p["er"]
        z_score = (val - mean) / std_dev if std_dev > 0 else 0.0

        if z_score >= z_threshold or (mean > 0 and val >= 2.5 * mean):
            anomalies.append({
                "post_id": p.get("post_id"),
                "type": "spike",
                "engagement_rate": round(val, 4),
                "baseline_mean": round(mean, 4),
                "deviation_pct": round(((val - mean) / mean) * 100.0, 2) if mean > 0 else 0.0,
                "reason": f"Engagement rate {val:.2f}% is significantly higher than historical average ({mean:.2f}%).",
            })
        elif z_score <= -1.5 or (mean > 0 and val <= 0.35 * mean):
            anomalies.append({
                "post_id": p.get("post_id"),
                "type": "drop",
                "engagement_rate": round(val, 4),
                "baseline_mean": round(mean, 4),
                "deviation_pct": round(((val - mean) / mean) * 100.0, 2) if mean > 0 else 0.0,
                "reason": f"Engagement rate {val:.2f}% is significantly lower than historical average ({mean:.2f}%).",
            })

    return anomalies
