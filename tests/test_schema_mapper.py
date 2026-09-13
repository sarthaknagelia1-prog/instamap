"""
tests/test_schema_mapper.py

Unit tests for backend.data.schema_mapper.
"""

from backend.data.schema_mapper import (
    map_record_keys,
    map_dataset,
    detect_available_and_missing,
    REQUIRED_FOR_ANALYSIS,
    CONTENT_TYPE_NORMALIZATION,
)


def test_map_record_keys_known_aliases():
    raw = {
        "media_id": "12345",
        "creatorId": "cr_99",
        "date": "2026-08-01T12:00:00Z",
        "format": "Reels",
        "num_likes": "150",
        "num_comments": "20",
        "num_shares": "5",
        "num_saves": "12",
        "unique_views": "2500",
        "description": "Awesome post!",
        "tags": ["ai", "growth"],
    }

    mapped = map_record_keys(raw)

    assert mapped["post_id"] == "12345"
    assert mapped["creator_id"] == "cr_99"
    assert mapped["timestamp"] == "2026-08-01T12:00:00Z"
    assert mapped["content_type"] == "reel"
    assert mapped["likes_count"] == "150"
    assert mapped["comments_count"] == "20"
    assert mapped["shares_count"] == "5"
    assert mapped["saves_count"] == "12"
    assert mapped["reach"] == "2500"
    assert mapped["caption_text"] == "Awesome post!"
    assert mapped["hashtags"] == ["ai", "growth"]


def test_map_record_keys_unmapped_keys_preserved():
    raw = {
        "post_id": "p1",
        "custom_sponsor": "BrandX",
        "internal_score": 9.5,
    }
    mapped = map_record_keys(raw)
    assert mapped["post_id"] == "p1"
    assert mapped["extra_custom_sponsor"] == "BrandX"
    assert mapped["extra_internal_score"] == 9.5


def test_content_type_normalization():
    examples = {
        "Reel": "reel",
        "reels": "reel",
        "video": "reel",
        "CAROUSEL": "carousel",
        "carousel_album": "carousel",
        "photo": "image",
        "static": "image",
        "story": "story",
        "stories": "story",
    }
    for raw_type, expected in examples.items():
        mapped = map_record_keys({"content_type": raw_type})
        assert mapped["content_type"] == expected


def test_detect_available_and_missing():
    records = [
        {"post_id": "p1", "timestamp": "2026-01-01", "content_type": "reel", "likes_count": 10},
        {"post_id": "p2", "timestamp": "2026-01-02", "content_type": "image", "comments_count": 5},
    ]
    detected = detect_available_and_missing(records)
    assert "post_id" in detected["available_features"]
    assert "timestamp" in detected["available_features"]
    assert "likes_count" in detected["available_features"]
    assert "comments_count" in detected["available_features"]
    # Shares were not populated in any record
    assert "shares_count" in detected["missing_features"]
