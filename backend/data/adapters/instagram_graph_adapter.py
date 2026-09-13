"""
backend/data/adapters/instagram_graph_adapter.py

Fetches media + insights data from the Meta (Instagram) Graph API.
Requires a long-lived access token with instagram_basic and
instagram_manage_insights permissions, plus the IG Business/Creator
Account ID connected to a Facebook Page.
"""

from __future__ import annotations
import os
import time
from typing import Any, Dict, List, Optional
import requests

from backend.config import settings
from backend.data.adapters.base_adapter import BaseAdapter

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
    "REEL": "reach,likes,comments,shares,saves,plays,total_interactions",
    "CAROUSEL_ALBUM": "reach,likes,comments,shares,saves",
    "IMAGE": "reach,likes,comments,shares,saves",
}


class InstagramGraphAdapter(BaseAdapter):
    source_name = "instagram_graph_api"

    def __init__(self, access_token: Optional[str] = None, ig_user_id: Optional[str] = None):
        self.access_token = access_token or settings.IG_ACCESS_TOKEN or os.environ.get("IG_ACCESS_TOKEN")
        self.ig_user_id = ig_user_id or settings.IG_USER_ID or os.environ.get("IG_USER_ID")
        if not self.access_token or not self.ig_user_id:
            raise ValueError(
                "InstagramGraphAdapter requires access_token and ig_user_id "
                "(pass directly or set IG_ACCESS_TOKEN / IG_USER_ID env vars)."
            )

    def _get(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        params = {**params, "access_token": self.access_token}
        response = requests.get(f"{GRAPH_API_BASE}/{path}", params=params, timeout=30)
        if response.status_code == 429:
            time.sleep(5)
            response = requests.get(f"{GRAPH_API_BASE}/{path}", params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def _list_media(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Paginates through the account's media."""
        media: List[Dict[str, Any]] = []
        params = {"fields": ",".join(MEDIA_FIELDS), "limit": min(limit, 100)}
        path = f"{self.ig_user_id}/media"

        while path and len(media) < limit:
            data = self._get(path.replace(GRAPH_API_BASE + "/", ""), params)
            media.extend(data.get("data", []))
            next_url = data.get("paging", {}).get("next")
            path = next_url if next_url else None
            params = {}

        return media[:limit]

    def _get_insights(self, media_id: str, media_type: str) -> Dict[str, Any]:
        """Fetches per-post insights; returns {} if unavailable."""
        metrics = INSIGHT_METRICS_BY_TYPE.get(media_type, INSIGHT_METRICS_BY_TYPE["IMAGE"])
        try:
            data = self._get(f"{media_id}/insights", {"metric": metrics})
            return {item["name"]: item["values"][0]["value"] for item in data.get("data", [])}
        except requests.HTTPError:
            return {}

    def fetch(self, limit: int = 50, include_insights: bool = True, **kwargs: Any) -> List[Dict[str, Any]]:
        raw_records: List[Dict[str, Any]] = []

        for post in self._list_media(limit=limit):
            record = {
                "post_id": post.get("id"),
                "caption": post.get("caption"),
                "media_type": post.get("media_product_type") or post.get("media_type"),
                "timestamp": post.get("timestamp"),
                "like_count": post.get("like_count"),
                "comments_count": post.get("comments_count"),
                "permalink": post.get("permalink"),
            }

            if include_insights and record["post_id"]:
                insights = self._get_insights(record["post_id"], record["media_type"] or "IMAGE")
                record.update(insights)

            raw_records.append(record)

        return raw_records
