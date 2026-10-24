"""
tests/test_meta_adapter.py

Unit and endpoint test suite for MetaAdapter and Meta Account ingestion.
"""

from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.data.adapters.meta_adapter import MetaAdapter
from backend.database.session import SessionLocal
from backend.database.models import Creator, Post

client = TestClient(app)


def test_parse_meta_business_suite_csv():
    csv_data = (
        "Post ID,Publish time,Permalink,Post type,Impressions,Reach,Likes and reactions,Comments,Shares,Saves\n"
        "179823451,2026-10-10 18:00:00,https://instagr.am/p/xyz,Reel,4500,3200,280,35,42,88\n"
        "179823452,2026-10-12 12:00:00,https://instagr.am/p/abc,Carousel,3100,2400,195,20,15,64\n"
    )
    records = MetaAdapter.parse_meta_export_archive(csv_data, filename="meta_business_suite_export.csv")
    assert len(records) == 2
    assert records[0]["post_id"] == "179823451"
    assert records[0]["content_type"] == "REEL"
    assert records[0]["reach"] == 3200
    assert records[0]["saves_count"] == 88
    assert records[1]["content_type"] == "CAROUSEL"


def test_parse_instagram_data_download_json():
    json_data = """[
        {
            "media": [
                {
                    "uri": "media/posts/202610/reel_sample.mp4",
                    "creation_timestamp": 1791820800,
                    "title": "How to scale your audience on Instagram #growth #creator"
                }
            ]
        }
    ]"""
    records = MetaAdapter.parse_meta_export_archive(json_data, filename="posts_1.json")
    assert len(records) == 1
    assert "meta_" in records[0]["post_id"]
    assert records[0]["content_type"] == "REEL"
    assert "scale your audience" in records[0]["caption_text"]


@patch("backend.data.adapters.meta_adapter.requests.get")
def test_fetch_account_posts_with_mock(mock_get):
    # Mock /me/accounts discovery
    mock_accounts = MagicMock()
    mock_accounts.status_code = 200
    mock_accounts.json.return_value = {
        "data": [
            {
                "id": "page_123",
                "instagram_business_account": {"id": "ig_biz_999", "username": "creator_biz"}
            }
        ]
    }

    # Mock /media
    mock_media = MagicMock()
    mock_media.status_code = 200
    mock_media.json.return_value = {
        "data": [
            {
                "id": "media_post_1",
                "caption": "My viral reel #growth",
                "media_type": "VIDEO",
                "media_product_type": "REELS",
                "timestamp": "2026-10-15T18:00:00+0000",
                "like_count": 350,
                "comments_count": 42,
                "permalink": "https://instagram.com/p/1",
            }
        ],
        "paging": {}
    }

    # Mock /insights
    mock_insights = MagicMock()
    mock_insights.status_code = 200
    mock_insights.json.return_value = {
        "data": [
            {"name": "reach", "values": [{"value": 4200}]},
            {"name": "saved", "values": [{"value": 115}]},
            {"name": "shares", "values": [{"value": 68}]},
        ]
    }

    mock_get.side_effect = [mock_accounts, mock_media, mock_insights]

    adapter = MetaAdapter(access_token="fake_token_123")
    posts = adapter.fetch_account_posts(limit=10)

    assert len(posts) == 1
    p = posts[0]
    assert p["post_id"] == "media_post_1"
    assert p["content_type"] == "REEL"
    assert p["likes_count"] == 350
    assert p["reach"] == 4200
    assert p["saves_count"] == 115


@patch("backend.api.routes_ingest.MetaAdapter.fetch_account_posts")
def test_ingest_meta_account_endpoint(mock_fetch):
    mock_fetch.return_value = [
        {
            "post_id": "meta_live_01",
            "content_type": "REEL",
            "timestamp": "2026-10-20T18:00:00Z",
            "caption_text": "Live imported Reel from user's account",
            "likes_count": 210,
            "comments_count": 25,
            "shares_count": 18,
            "saves_count": 45,
            "reach": 3100,
            "impressions": 4500,
        }
    ]

    db = SessionLocal()
    c_id = "meta_test_creator"
    try:
        if not db.get(Creator, c_id):
            db.add(Creator(id=c_id, workspace_id="default"))
            db.commit()
        db.query(Post).filter_by(creator_id=c_id).delete()
        db.commit()

        payload = {
            "creator_id": c_id,
            "access_token": "valid_user_meta_token",
            "limit": 10,
        }
        resp = client.post("/data/ingest/meta-account", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["data_ready"] is True
        assert data["inserted_count"] == 1
    finally:
        db.close()
