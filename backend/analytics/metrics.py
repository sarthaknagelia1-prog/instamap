"""
backend/analytics/metrics.py

Deterministic engagement metrics calculation:
- Engagement rate
- Save rate
- Share rate
- Reach efficiency
- Per-content-type breakdowns
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional


def calculate_post_engagement_rate(post: Dict[str, Any]) -> Optional[float]:
    """
    Computes post engagement rate.
    Uses reach as denominator if available, falling back to impressions.
    Returns engagement rate as a percentage rounded to 4 decimal places, or None if no denominator.
    """
    likes = post.get("likes_count") or 0
    comments = post.get("comments_count") or 0
    shares = post.get("shares_count") or 0
    saves = post.get("saves_count") or 0
    interactions = likes + comments + shares + saves

    denominator = post.get("reach") or post.get("impressions")
    if denominator and denominator > 0:
        return round((interactions / denominator) * 100.0, 4)

    return None


def calculate_post_metrics(post: Dict[str, Any]) -> Dict[str, Optional[float]]:
    """Calculates all individual rate metrics for a post."""
    likes = post.get("likes_count") or 0
    comments = post.get("comments_count") or 0
    shares = post.get("shares_count") or 0
    saves = post.get("saves_count") or 0
    reach = post.get("reach")
    impressions = post.get("impressions")

    denominator = reach or impressions
    has_denom = denominator is not None and denominator > 0

    engagement_rate = calculate_post_engagement_rate(post)
    save_rate = round(((saves or 0) / denominator) * 100.0, 4) if has_denom and post.get("saves_count") is not None else None
    share_rate = round(((shares or 0) / denominator) * 100.0, 4) if has_denom and post.get("shares_count") is not None else None

    reach_efficiency = None
    if reach and impressions and impressions > 0:
        reach_efficiency = round((reach / impressions) * 100.0, 2)

    return {
        "engagement_rate": engagement_rate,
        "save_rate": save_rate,
        "share_rate": share_rate,
        "reach_efficiency": reach_efficiency,
    }


def calculate_aggregate_metrics(posts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregates metrics across all posts for a creator, including
    content-type breakdowns and overall averages.
    """
    if not posts:
        return {
            "total_posts": 0,
            "average_engagement_rate": 0.0,
            "top_content_type": "unknown",
            "content_type_breakdown": {},
            "top_performing_posts": [],
        }

    # Group by content type
    by_type: Dict[str, List[Dict[str, Any]]] = {}
    total_er_sum = 0.0
    valid_er_count = 0

    enriched_posts: List[Dict[str, Any]] = []

    for p in posts:
        p_copy = dict(p)
        er = calculate_post_engagement_rate(p_copy)
        p_copy["engagement_rate"] = er
        enriched_posts.append(p_copy)

        if er is not None:
            total_er_sum += er
            valid_er_count += 1

        ctype = str(p_copy.get("content_type") or "unknown").lower()
        by_type.setdefault(ctype, []).append(p_copy)

    avg_er = round(total_er_sum / valid_er_count, 4) if valid_er_count > 0 else 0.0

    breakdown: Dict[str, Dict[str, Any]] = {}
    best_type = "unknown"
    highest_type_er = -1.0

    for ctype, type_posts in by_type.items():
        type_er_sum = 0.0
        type_er_valid = 0
        likes_sum = 0
        comments_sum = 0
        saves_sum = 0
        shares_sum = 0
        reach_sum = 0

        for p in type_posts:
            if p.get("engagement_rate") is not None:
                type_er_sum += p["engagement_rate"]
                type_er_valid += 1
            likes_sum += p.get("likes_count") or 0
            comments_sum += p.get("comments_count") or 0
            saves_sum += p.get("saves_count") or 0
            shares_sum += p.get("shares_count") or 0
            reach_sum += p.get("reach") or 0

        count = len(type_posts)
        type_avg_er = round(type_er_sum / type_er_valid, 4) if type_er_valid > 0 else 0.0

        breakdown[ctype] = {
            "count": count,
            "average_engagement_rate": type_avg_er,
            "average_likes": round(likes_sum / count, 1),
            "average_comments": round(comments_sum / count, 1),
            "average_saves": round(saves_sum / count, 1),
            "average_shares": round(shares_sum / count, 1),
            "average_reach": round(reach_sum / count, 1),
        }

        if type_avg_er > highest_type_er:
            highest_type_er = type_avg_er
            best_type = ctype

    # Sort posts by engagement_rate desc for top posts
    sorted_posts = sorted(
        enriched_posts,
        key=lambda x: (x.get("engagement_rate") or 0.0),
        reverse=True,
    )

    top_posts = [
        {
            "post_id": p.get("post_id"),
            "content_type": p.get("content_type"),
            "timestamp": p.get("timestamp"),
            "engagement_rate": p.get("engagement_rate"),
            "reach": p.get("reach"),
            "likes_count": p.get("likes_count"),
            "saves_count": p.get("saves_count"),
            "caption_text": p.get("caption_text"),
        }
        for p in sorted_posts[:5]
    ]

    return {
        "total_posts": len(posts),
        "average_engagement_rate": avg_er,
        "top_content_type": best_type,
        "content_type_breakdown": breakdown,
        "top_performing_posts": top_posts,
    }
