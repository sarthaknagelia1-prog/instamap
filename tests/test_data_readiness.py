"""
tests/test_data_readiness.py

Unit tests for backend.data.ingestion.data_readiness_agent.
"""

from backend.data.ingestion.data_readiness_agent import (
    run,
    _dedupe,
    _validate_timestamps,
    _coerce_numeric,
    _calculate_quality_score,
)


def test_dedupe_posts():
    records = [
        {"post_id": "p1", "caption": "first"},
        {"post_id": "p2", "caption": "second"},
        {"post_id": "p1", "caption": "duplicate"},
    ]
    deduped, count = _dedupe(records)
    assert count == 1
    assert len(deduped) == 2
    assert deduped[0]["post_id"] == "p1"
    assert deduped[1]["post_id"] == "p2"


def test_validate_timestamps():
    records = [
        {"post_id": "p1", "timestamp": "2026-08-01T18:00:00Z"},
        {"post_id": "p2", "timestamp": "invalid-date-string"},
        {"post_id": "p3", "timestamp": None},
    ]
    validated, invalid_count = _validate_timestamps(records)
    assert invalid_count == 1
    assert validated[0]["timestamp"] == "2026-08-01T18:00:00+00:00"
    assert validated[1]["timestamp"] == "invalid-date-string"
    assert validated[2]["timestamp"] is None


def test_coerce_numeric():
    record = {
        "likes_count": "150",
        "comments_count": "25.0",
        "shares_count": "",
        "saves_count": "invalid",
    }
    _coerce_numeric(record, "likes_count")
    _coerce_numeric(record, "comments_count")
    _coerce_numeric(record, "shares_count")
    _coerce_numeric(record, "saves_count")

    assert record["likes_count"] == 150
    assert record["comments_count"] == 25
    assert record["shares_count"] is None
    assert record["saves_count"] is None


def test_data_readiness_run_success():
    payload = {
        "creator_id": "creator_123",
        "source": "csv_upload",
        "raw_data": [
            {
                "id": "post_1",
                "type": "reel",
                "timestamp": "2026-08-01T18:00:00Z",
                "like_count": 200,
                "comments": 15,
                "reach": 1500,
            },
            {
                "id": "post_2",
                "type": "carousel",
                "timestamp": "2026-08-03T12:00:00Z",
                "like_count": 120,
                "comments": 8,
                "reach": 1000,
            }
        ]
    }
    result = run(payload, quality_threshold=0.4)
    assert result["data_ready"] is True
    assert result["quality_score"] > 0.4
    assert result["record_count"] == 2
    assert "processed_data" in result
    assert len(result["processed_data"]) == 2


def test_data_readiness_run_missing_required():
    # Missing 'timestamp' and 'comments_count' entirely
    payload = {
        "creator_id": "creator_123",
        "source": "csv_upload",
        "raw_data": [
            {"id": "post_1", "type": "reel", "like_count": 200}
        ]
    }
    result = run(payload)
    assert result["data_ready"] is False
    assert "timestamp" in result["missing_features"]
    assert "comments_count" in result["missing_features"]
    assert "processed_data" not in result
