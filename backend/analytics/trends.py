"""
backend/analytics/trends.py

Trend detection, rolling metrics, week-over-week analysis,
and optimal posting window calculations.
"""

from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

from backend.analytics.metrics import calculate_post_engagement_rate


def _parse_dt(val: Any) -> Optional[datetime]:
    if not val:
        return None
    if isinstance(val, datetime):
        return val if val.tzinfo else val.replace(tzinfo=timezone.utc)
    try:
        clean_str = str(val).replace("Z", "+00:00")
        return datetime.fromisoformat(clean_str)
    except (ValueError, TypeError):
        return None


def detect_trends(posts: List[Dict[str, Any]], rolling_window_size: int = 5) -> Dict[str, Any]:
    """
    Analyzes historical posts chronologically to compute:
    - Rolling average engagement rate
    - Week-over-week delta
    - Overall trend classification ("improving", "declining", "stable")
    """
    if not posts:
        return {
            "recent_trend": "stable",
            "week_over_week_delta_pct": 0.0,
            "rolling_average_er": [],
        }

    # Enrich with parsed datetime and engagement rate
    valid_posts = []
    for p in posts:
        dt = _parse_dt(p.get("timestamp"))
        er = p.get("engagement_rate")
        if er is None:
            er = calculate_post_engagement_rate(p)
        if dt and er is not None:
            valid_posts.append({**p, "dt": dt, "er": er})

    if not valid_posts:
        return {
            "recent_trend": "stable",
            "week_over_week_delta_pct": 0.0,
            "rolling_average_er": [],
        }

    # Sort chronologically ascending
    valid_posts.sort(key=lambda x: x["dt"])

    # Rolling averages
    rolling_averages = []
    er_values = [p["er"] for p in valid_posts]
    for i in range(len(er_values)):
        start_idx = max(0, i - rolling_window_size + 1)
        window = er_values[start_idx : i + 1]
        rolling_averages.append({
            "post_id": valid_posts[i].get("post_id"),
            "timestamp": valid_posts[i]["dt"].isoformat(),
            "rolling_er": round(sum(window) / len(window), 4),
        })

    # Week-over-week comparison using timestamps
    latest_dt = valid_posts[-1]["dt"]
    seven_days_ago = latest_dt - timedelta(days=7)
    fourteen_days_ago = latest_dt - timedelta(days=14)

    recent_week = [p["er"] for p in valid_posts if p["dt"] > seven_days_ago]
    prior_week = [p["er"] for p in valid_posts if fourteen_days_ago < p["dt"] <= seven_days_ago]

    # Fallback to splitting posts into two halves if date span is too short
    if not prior_week and len(valid_posts) >= 4:
        mid = len(valid_posts) // 2
        prior_week = [p["er"] for p in valid_posts[:mid]]
        recent_week = [p["er"] for p in valid_posts[mid:]]

    wow_delta_pct = 0.0
    if recent_week and prior_week:
        recent_avg = sum(recent_week) / len(recent_week)
        prior_avg = sum(prior_week) / len(prior_week)
        if prior_avg > 0:
            wow_delta_pct = round(((recent_avg - prior_avg) / prior_avg) * 100.0, 2)
        elif recent_avg > 0:
            wow_delta_pct = 100.0

    # Trend classification
    if wow_delta_pct >= 5.0:
        recent_trend = "improving"
    elif wow_delta_pct <= -5.0:
        recent_trend = "declining"
    else:
        recent_trend = "stable"

    return {
        "recent_trend": recent_trend,
        "week_over_week_delta_pct": wow_delta_pct,
        "rolling_average_er": rolling_averages,
    }


def find_best_posting_window(posts: List[Dict[str, Any]]) -> str:
    """
    Groups posts by day of the week and 3-hour time blocks
    to determine which window produces the highest average engagement rate.
    Returns human-readable window e.g. "Wednesday 18:00 - 21:00 UTC".
    """
    DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    buckets = defaultdict(list)

    for p in posts:
        dt = _parse_dt(p.get("timestamp"))
        if not dt:
            continue

        er = p.get("engagement_rate")
        if er is None:
            er = calculate_post_engagement_rate(p)
        if er is None:
            continue

        day_name = DAYS[dt.weekday()]
        hour_block = (dt.hour // 3) * 3
        bucket_key = (day_name, hour_block)
        buckets[bucket_key].append(er)

    if not buckets:
        return "Insufficient timestamp data"

    best_key = None
    highest_avg = -1.0

    for key, er_list in buckets.items():
        avg_er = sum(er_list) / len(er_list)
        if avg_er > highest_avg:
            highest_avg = avg_er
            best_key = key

    if best_key:
        day, start_h = best_key
        end_h = start_h + 3
        return f"{day} {start_h:02d}:00 - {end_h:02d}:00 UTC"

    return "Insufficient timestamp data"
