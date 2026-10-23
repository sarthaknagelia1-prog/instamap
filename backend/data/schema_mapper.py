"""
backend/data/schema_mapper.py

Maps arbitrary/incoming dataset column names to the canonical schema used
throughout the Instagram Growth Engine.

Different export sources (Meta Graph API, third-party analytics tools,
manual CSV exports) use different column names for the same concept.
This module resolves that into one consistent internal representation.
"""

from __future__ import annotations
from typing import Any, Dict, List

# Canonical field -> list of known aliases seen across data sources.
FIELD_ALIASES: Dict[str, List[str]] = {
    "post_id": [
        "post_id", "id", "media_id", "postid", "mediaid", "post_url",
        "url", "permalink", "link", "post link", "post id", "media id"
    ],
    "creator_id": [
        "creator_id", "account_id", "user_id", "creatorid", "accountid",
        "profile", "profile_name", "username", "account", "channel"
    ],
    "timestamp": [
        "timestamp", "created_at", "posted_at", "date", "publish_time",
        "publish date", "published date", "published at", "created time",
        "time", "date (gmt)", "post date", "creation date"
    ],
    "content_type": [
        "content_type", "type", "media_type", "format", "post_type",
        "post type", "content type", "media type", "format type"
    ],
    "likes_count": [
        "likes", "like_count", "likes_count", "num_likes", "reactions",
        "favorites", "like", "number of likes"
    ],
    "comments_count": [
        "comments", "comment_count", "comments_count", "num_comments",
        "replies", "comment", "number of comments"
    ],
    "shares_count": [
        "shares", "share_count", "shares_count", "num_shares", "retweets/shares",
        "reposts", "forward_count", "share", "number of shares"
    ],
    "saves_count": [
        "saves", "save_count", "saves_count", "num_saves", "bookmarks",
        "saved", "save", "number of saves"
    ],
    "reach": [
        "reach", "impressions_reach", "unique_views", "accounts reached",
        "lifetime post total reach", "total reach", "unique reach", "post reach"
    ],
    "impressions": [
        "impressions", "views", "video_views", "play_count", "total impressions",
        "lifetime post total impressions", "plays", "post impressions"
    ],
    "caption_text": [
        "caption", "caption_text", "text", "description", "message",
        "post text", "content", "copy", "title"
    ],
    "hashtags": [
        "hashtags", "tags", "hashtag_list", "tag_list", "keywords"
    ],
    "watch_time_avg": [
        "avg_watch_time", "watch_time_avg", "average_watch_time",
        "watch time", "avg view duration", "retention"
    ],
}

# Fields the system needs at minimum to run performance analysis.
REQUIRED_FOR_ANALYSIS = [
    "post_id",
    "timestamp",
    "content_type",
    "likes_count",
    "comments_count",
]

# Fields that are useful but not blocking.
OPTIONAL_FEATURES = [
    "shares_count",
    "saves_count",
    "reach",
    "impressions",
    "caption_text",
    "hashtags",
    "watch_time_avg",
]

# Content-type strings normalized to a fixed vocabulary.
CONTENT_TYPE_NORMALIZATION = {
    "reel": "reel", "reels": "reel", "video": "reel", "clip": "reel", "short": "reel",
    "carousel": "carousel", "carousel_album": "carousel", "album": "carousel", "slideshow": "carousel",
    "image": "image", "photo": "image", "post": "image", "static": "image", "picture": "image",
    "story": "story", "stories": "story",
}


def detect_source_platform(headers: List[str]) -> str:
    """
    Infers the origin tool/platform from the header names in the export.
    Useful for audit logs and source-specific handling.
    """
    lowered = {h.strip().lower() for h in headers}

    if any("lifetime post total" in h for h in lowered):
        return "sprout_social"
    if any("date (gmt)" in h or "total impressions" in h for h in lowered):
        return "hootsuite"
    if any("accounts reached" in h or "publish time" in h for h in lowered):
        return "meta_business_suite"
    if any("permalink" in h for h in lowered) and any("reactions" in h for h in lowered):
        return "later"
    if any("metricool" in h for h in lowered):
        return "metricool"

    return "generic_csv_or_table"




def _build_reverse_lookup() -> Dict[str, str]:
    """Builds alias -> canonical_field map, case-insensitive."""
    reverse: Dict[str, str] = {}
    for canonical, aliases in FIELD_ALIASES.items():
        for alias in aliases:
            reverse[alias.strip().lower()] = canonical
    return reverse


_REVERSE_LOOKUP = _build_reverse_lookup()


def map_record_keys(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Maps a single raw record's keys to canonical field names.
    Unrecognized keys are preserved under 'extra_<original_key>' so no
    data is silently dropped.
    """
    mapped: Dict[str, Any] = {}
    for raw_key, value in record.items():
        canonical = _REVERSE_LOOKUP.get(str(raw_key).strip().lower())
        if canonical:
            mapped[canonical] = value
        else:
            mapped[f"extra_{raw_key}"] = value

    if "content_type" in mapped and isinstance(mapped["content_type"], str):
        normalized = CONTENT_TYPE_NORMALIZATION.get(
            mapped["content_type"].strip().lower(), mapped["content_type"].strip().lower()
        )
        mapped["content_type"] = normalized

    return mapped


def map_dataset(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Maps a full list of raw records to canonical schema."""
    return [map_record_keys(r) for r in records]


def detect_available_and_missing(mapped_records: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Inspects mapped records to see which required and optional features
    actually contain data (at least one non-null, non-empty value across rows).
    """
    all_tracked = REQUIRED_FOR_ANALYSIS + OPTIONAL_FEATURES
    available: List[str] = []
    missing: List[str] = []

    for field in all_tracked:
        has_value = any(
            r.get(field) is not None and r.get(field) != ""
            for r in mapped_records
        )
        if has_value:
            available.append(field)
        else:
            missing.append(field)

    return {
        "available_features": available,
        "missing_features": missing,
    }
