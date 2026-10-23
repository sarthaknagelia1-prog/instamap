"""
tests/test_creators_and_analytics.py

Tests for:
- Creator listing and details endpoints
- Paginated post browser with sorting and filtering
- Ingestion logs endpoint
- Time-series analytics endpoint
- Dashboard summary caching
"""

def test_creators_endpoints(client):
    # Ingest data for creator_c1
    payload = {
        "creator_id": "creator_c1",
        "raw_data": [
            {"post_id": "c1_p1", "date": "2026-10-01T12:00:00Z", "type": "reel", "likes": 200, "comments": 20},
            {"post_id": "c1_p2", "date": "2026-10-02T12:00:00Z", "type": "image", "likes": 100, "comments": 10},
            {"post_id": "c1_p3", "date": "2026-10-03T12:00:00Z", "type": "reel", "likes": 300, "comments": 30},
        ],
        "quality_threshold": 0.5,
    }
    client.post("/data/ingest", json=payload)

    # 1. Test GET /creators
    res = client.get("/creators")
    assert res.status_code == 200
    creators = res.json()
    assert any(c["id"] == "creator_c1" for c in creators)
    c1 = next(c for c in creators if c["id"] == "creator_c1")
    assert c1["total_posts"] == 3

    # 2. Test GET /creators/creator_c1
    res_single = client.get("/creators/creator_c1")
    assert res_single.status_code == 200
    assert res_single.json()["total_posts"] == 3

    # 3. Test GET /creators/{id}/posts with filtering
    res_posts_reel = client.get("/creators/creator_c1/posts?content_type=reel")
    assert res_posts_reel.status_code == 200
    data_reels = res_posts_reel.json()
    assert data_reels["total_count"] == 2
    assert all(p["content_type"] == "reel" for p in data_reels["posts"])

    # 4. Test GET /creators/{id}/posts with sorting by likes desc
    res_sort = client.get("/creators/creator_c1/posts?sort_by=likes&order=desc")
    assert res_sort.status_code == 200
    posts_sorted = res_sort.json()["posts"]
    assert posts_sorted[0]["likes_count"] >= posts_sorted[1]["likes_count"]

    # 5. Test GET /creators/{id}/ingestion-logs
    res_logs = client.get("/creators/creator_c1/ingestion-logs")
    assert res_logs.status_code == 200
    logs = res_logs.json()
    assert len(logs) >= 1
    assert logs[0]["data_ready"] is True


def test_analytics_time_series_and_caching(client):
    payload = {
        "creator_id": "creator_ts",
        "raw_data": [
            {"post_id": "ts_1", "date": "2026-10-01T10:00:00Z", "type": "reel", "likes": 150, "comments": 15, "reach": 2000},
            {"post_id": "ts_2", "date": "2026-10-02T10:00:00Z", "type": "carousel", "likes": 220, "comments": 25, "reach": 3000},
        ],
        "quality_threshold": 0.5,
    }
    client.post("/data/ingest", json=payload)

    # Test time-series endpoint
    res_ts = client.get("/analytics/time-series?creator_id=creator_ts")
    assert res_ts.status_code == 200
    ts_data = res_ts.json()
    assert ts_data["creator_id"] == "creator_ts"
    assert ts_data["total_data_points"] == 2
    assert ts_data["series"][0]["post_id"] == "ts_1"

    # Test summary caching
    res_sum1 = client.get("/analytics/summary?creator_id=creator_ts")
    assert res_sum1.status_code == 200
    res_sum2 = client.get("/analytics/summary?creator_id=creator_ts")
    assert res_sum2.status_code == 200
    assert res_sum1.json() == res_sum2.json()
