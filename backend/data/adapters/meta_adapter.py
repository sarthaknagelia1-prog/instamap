"""
backend/data/adapters/meta_adapter.py

Comprehensive Meta (Instagram) Data Adapter.
Enables creators to import data from their own Instagram account:
1. Direct Meta Graph API Ingestion:
   - User Access Token or Page/IG Access Token sync.
   - Auto-discovers Instagram Business / Creator Account ID from `/me/accounts` if not provided.
   - Fetches media records and per-post insights (reach, impressions, saves, shares, likes, comments).
2. Meta Business Suite & Official Instagram Data Archive Parsers:
   - Official Meta Business Suite CSV exports (with columns like "Post ID", "Publish time", "Reach", "Likes and reactions", "Saves").
   - Instagram "Download Your Information" JSON exports (posts_1.json, content.json).
"""

from __future__ import annotations
import csv
import io
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import requests

from backend.data.adapters.base_adapter import BaseAdapter

logger = logging.getLogger(__name__)

GRAPH_API_VERSION = "v19.0"
GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

MEDIA_FIELDS = [
    "id",
    "caption",
    "media_type",
    "media_product_type",
    "timestamp",
    "like_count",
    "comments_count",
    "permalink",
]

INSIGHT_METRICS_BY_TYPE = {
    "REEL": "reach,likes,comments,shares,saves,plays",
    "VIDEO": "reach,likes,comments,shares,saves,plays",
    "CAROUSEL_ALBUM": "reach,likes,comments,shares,saves",
    "IMAGE": "reach,likes,comments,shares,saves",
}


class MetaAdapter(BaseAdapter):
    """Adapter for importing account data directly via Meta Graph API or Meta export archives."""

    source_name = "meta_account_import"

    def __init__(self, access_token: Optional[str] = None, ig_user_id: Optional[str] = None):
        self.access_token = access_token
        self.ig_user_id = ig_user_id

    def _get(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        params = {**params, "access_token": self.access_token}
        url = f"{GRAPH_API_BASE}/{path.lstrip('/')}"
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 429:
            time.sleep(3)
            response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def discover_ig_user_id(self) -> Optional[str]:
        """Auto-discovers connected Instagram Business/Creator Account ID from the user token."""
        if self.ig_user_id:
            return self.ig_user_id

        try:
            # First check /me/accounts for Facebook Pages connected to Instagram
            accounts_data = self._get("me/accounts", {"fields": "instagram_business_account{id,username,name}"})
            for page in accounts_data.get("data", []):
                ig_acc = page.get("instagram_business_account")
                if ig_acc and ig_acc.get("id"):
                    self.ig_user_id = ig_acc["id"]
                    return self.ig_user_id
        except Exception as e:
            logger.warning("Could not auto-discover IG account from /me/accounts: %s", e)

        try:
            # Fallback to direct /me?fields=id
            me_data = self._get("me", {"fields": "id,name"})
            if me_data.get("id"):
                self.ig_user_id = me_data["id"]
                return self.ig_user_id
        except Exception as e:
            logger.warning("Could not resolve /me: %s", e)

        return None

    def fetch_account_posts(self, limit: int = 50, include_insights: bool = True) -> List[Dict[str, Any]]:
        """
        Fetches media and insights from the Meta Graph API and converts
        them into standard normalized InstaMap post dictionaries.
        """
        if not self.access_token:
            raise ValueError("Meta access_token is required for direct account fetch.")

        ig_id = self.discover_ig_user_id()
        if not ig_id:
            raise ValueError("Unable to determine Instagram Account ID. Please provide ig_user_id explicitly.")

        raw_media: List[Dict[str, Any]] = []
        path = f"{ig_id}/media"
        params = {"fields": ",".join(MEDIA_FIELDS), "limit": min(limit, 100)}

        while path and len(raw_media) < limit:
            clean_path = path.replace(GRAPH_API_BASE + "/", "").lstrip("/")
            data = self._get(clean_path, params)
            raw_media.extend(data.get("data", []))
            next_url = data.get("paging", {}).get("next")
            path = next_url if next_url else None
            params = {}

        normalized: List[Dict[str, Any]] = []
        for post in raw_media[:limit]:
            post_id = post.get("id")
            media_type = (post.get("media_product_type") or post.get("media_type") or "IMAGE").upper()
            if "REEL" in media_type:
                content_type = "REEL"
            elif "CAROUSEL" in media_type:
                content_type = "CAROUSEL"
            elif "VIDEO" in media_type:
                content_type = "VIDEO"
            else:
                content_type = "IMAGE"

            record: Dict[str, Any] = {
                "post_id": post_id,
                "content_type": content_type,
                "timestamp": post.get("timestamp"),
                "caption_text": post.get("caption") or "",
                "likes_count": post.get("like_count") or 0,
                "comments_count": post.get("comments_count") or 0,
                "shares_count": 0,
                "saves_count": 0,
                "reach": None,
                "impressions": None,
                "permalink": post.get("permalink"),
            }

            if include_insights and post_id:
                try:
                    metrics_str = INSIGHT_METRICS_BY_TYPE.get(content_type, INSIGHT_METRICS_BY_TYPE["IMAGE"])
                    insights_data = self._get(f"{post_id}/insights", {"metric": metrics_str})
                    for item in insights_data.get("data", []):
                        val = item.get("values", [{}])[0].get("value")
                        name = item.get("name")
                        if name == "reach":
                            record["reach"] = val
                        elif name in ("impressions", "plays"):
                            record["impressions"] = val
                        elif name == "saved" or name == "saves":
                            record["saves_count"] = val
                        elif name == "shares":
                            record["shares_count"] = val
                except Exception as e:
                    logger.debug("Insights fetch failed for post %s: %s", post_id, e)

            normalized.append(record)

        return normalized

    @classmethod
    def parse_meta_export_archive(cls, content_str: str, filename: str = "") -> List[Dict[str, Any]]:
        """
        Parses an official Meta export file:
        - Meta Business Suite CSV
        - Instagram Data Download JSON (e.g. posts_1.json, content.json)
        """
        filename_lower = filename.lower()

        # If JSON or starts with { / [
        trimmed = content_str.strip()
        if filename_lower.endswith(".json") or trimmed.startswith(("{", "[")):
            return cls._parse_meta_json_export(trimmed)

        # Otherwise parse as CSV
        return cls._parse_meta_csv_export(trimmed)

    @classmethod
    def _parse_meta_json_export(cls, json_str: str) -> List[Dict[str, Any]]:
        """Parses Instagram Download Your Information JSON format."""
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON data export: {e}")

        items = data if isinstance(data, list) else data.get("media", data.get("posts", []))
        normalized: List[Dict[str, Any]] = []

        for idx, item in enumerate(items):
            # Check structure: item can have sub-media array or direct keys
            media_list = item.get("media", [item])
            for m_idx, media_item in enumerate(media_list):
                ts_val = media_item.get("creation_timestamp") or item.get("creation_timestamp")
                timestamp_str = None
                if ts_val:
                    try:
                        timestamp_str = datetime.fromtimestamp(float(ts_val), tz=timezone.utc).isoformat()
                    except Exception:
                        timestamp_str = str(ts_val)

                caption = media_item.get("title") or item.get("title") or media_item.get("caption") or ""
                uri = media_item.get("uri") or f"ig_post_{idx}_{m_idx}"
                post_id = f"meta_{abs(hash(uri + str(ts_val)))}"

                # Determine format from uri or media_metadata
                uri_lower = uri.lower()
                content_type = "IMAGE"
                if "reel" in uri_lower:
                    content_type = "REEL"
                elif "video" in uri_lower or ".mp4" in uri_lower or media_item.get("video_metadata"):
                    content_type = "VIDEO"
                elif len(media_list) > 1:
                    content_type = "CAROUSEL"

                normalized.append({
                    "post_id": post_id,
                    "content_type": content_type,
                    "timestamp": timestamp_str,
                    "caption_text": caption,
                    "likes_count": media_item.get("like_count") or 0,
                    "comments_count": media_item.get("comment_count") or 0,
                    "shares_count": 0,
                    "saves_count": 0,
                    "reach": None,
                    "impressions": None,
                })

        return normalized

    @classmethod
    def _parse_meta_csv_export(cls, csv_str: str) -> List[Dict[str, Any]]:
        """Parses Meta Business Suite CSV exports."""
        reader = csv.DictReader(io.StringIO(csv_str))
        rows = list(reader)
        if not rows:
            return []

        normalized: List[Dict[str, Any]] = []
        for idx, row in enumerate(rows):
            # Look up keys with case-insensitive matching
            clean_row = {k.strip().lower(): v for k, v in row.items() if k}

            post_id = clean_row.get("post id") or clean_row.get("post_id") or clean_row.get("id") or f"meta_csv_{idx+1}"
            ts = clean_row.get("publish time") or clean_row.get("published date") or clean_row.get("date") or clean_row.get("timestamp")
            caption = clean_row.get("description") or clean_row.get("caption") or clean_row.get("message") or clean_row.get("title") or ""
            p_type = (clean_row.get("post type") or clean_row.get("type") or "IMAGE").upper()

            if "REEL" in p_type:
                content_type = "REEL"
            elif "CAROUSEL" in p_type or "ALBUM" in p_type:
                content_type = "CAROUSEL"
            elif "VIDEO" in p_type:
                content_type = "VIDEO"
            else:
                content_type = "IMAGE"

            def to_int(val: Any) -> Optional[int]:
                if not val:
                    return None
                try:
                    return int(float(str(val).replace(",", "").strip()))
                except Exception:
                    return None

            likes = to_int(clean_row.get("likes and reactions") or clean_row.get("likes") or clean_row.get("like_count")) or 0
            comments = to_int(clean_row.get("comments") or clean_row.get("comments_count")) or 0
            shares = to_int(clean_row.get("shares") or clean_row.get("shares_count")) or 0
            saves = to_int(clean_row.get("saves") or clean_row.get("saves_count")) or 0
            reach = to_int(clean_row.get("reach") or clean_row.get("lifetime post total reach"))
            impressions = to_int(clean_row.get("impressions") or clean_row.get("lifetime post total impressions") or clean_row.get("plays"))

            normalized.append({
                "post_id": str(post_id),
                "content_type": content_type,
                "timestamp": ts,
                "caption_text": caption,
                "likes_count": likes,
                "comments_count": comments,
                "shares_count": shares,
                "saves_count": saves,
                "reach": reach,
                "impressions": impressions,
                "permalink": clean_row.get("permalink") or clean_row.get("url"),
            })

        return normalized

    def fetch(self, limit: int = 50, **kwargs: Any) -> List[Dict[str, Any]]:
        """BaseAdapter contract implementation."""
        return self.fetch_account_posts(limit=limit)
