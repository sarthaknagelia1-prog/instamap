"""
backend/data/ingestion/data_readiness_agent.py

Implements Agent 1 — Data Readiness Agent.

Responsibilities:
- Map schemas (delegates to schema_mapper).
- Identify missing values / duplicates.
- Validate timestamps.
- Normalize engagement metrics.
- Calculate a data coverage / quality score.

The agent never fabricates missing data — if something is unavailable,
it is reported as missing rather than inferred.
"""

from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from backend.data.schema_mapper import (
    map_dataset,
    detect_available_and_missing,
    REQUIRED_FOR_ANALYSIS,
    OPTIONAL_FEATURES,
)

ALL_TRACKED_FIELDS = REQUIRED_FOR_ANALYSIS + OPTIONAL_FEATURES


def _parse_timestamp(value: Any) -> datetime | None:
    """Best-effort ISO-8601 timestamp parse. Returns None if invalid/missing."""
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        text = str(value).replace("Z", "+00:00")
        return datetime.fromisoformat(text)
    except (ValueError, TypeError):
        return None


def _coerce_numeric(record: Dict[str, Any], field: str) -> None:
    """Coerces a metric field to int, defaulting invalid/missing to None (not 0)."""
    if field not in record:
        return
    value = record[field]
    if value is None or value == "":
        record[field] = None
        return
    try:
        record[field] = int(float(value))
    except (ValueError, TypeError):
        record[field] = None


def _dedupe(records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """Removes exact-duplicate posts based on post_id (or full-row fallback)."""
    seen = set()
    deduped = []
    duplicate_count = 0

    for record in records:
        key = record.get("post_id") or tuple(sorted(record.items(), key=lambda kv: str(kv[0])))
        if key in seen:
            duplicate_count += 1
            continue
        seen.add(key)
        deduped.append(record)

    return deduped, duplicate_count


def _validate_timestamps(records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """Parses/normalizes timestamps; counts records with invalid timestamps."""
    invalid_count = 0
    for record in records:
        parsed = _parse_timestamp(record.get("timestamp"))
        if parsed is None and "timestamp" in record and record["timestamp"] not in (None, ""):
            invalid_count += 1
        record["timestamp"] = parsed.isoformat() if parsed else record.get("timestamp")
    return records, invalid_count


def _calculate_quality_score(
    mapped_records: List[Dict[str, Any]],
    available_features: List[str],
    duplicate_count: int,
    invalid_timestamp_count: int,
    original_count: int,
) -> float:
    """
    Weighted quality score in [0, 1]:
      - 60% field coverage (of ALL_TRACKED_FIELDS)
      - 25% row completeness (required fields populated per row)
      - 15% cleanliness (penalize duplicates / bad timestamps)
    """
    if original_count == 0:
        return 0.0

    coverage_score = len(available_features) / len(ALL_TRACKED_FIELDS)

    complete_rows = sum(
        1 for r in mapped_records
        if all(r.get(f) is not None and r.get(f) != "" for f in REQUIRED_FOR_ANALYSIS)
    )
    completeness_score = complete_rows / max(len(mapped_records), 1)

    dirty_ratio = (duplicate_count + invalid_timestamp_count) / max(original_count, 1)
    cleanliness_score = max(0.0, 1.0 - dirty_ratio)

    score = (0.60 * coverage_score) + (0.25 * completeness_score) + (0.15 * cleanliness_score)
    return round(min(max(score, 0.0), 1.0), 2)


def run(creator_data: Dict[str, Any], quality_threshold: float = 0.5) -> Dict[str, Any]:
    """
    Main entry point for the Data Readiness Agent.

    Args:
        creator_data: {
            "creator_id": str,
            "source": str,
            "raw_data": List[dict]   # raw, unmapped records
        }
        quality_threshold: minimum quality_score required for data_ready=True

    Returns:
        {
            "data_ready": bool,
            "quality_score": float,
            "missing_features": [...],
            "available_features": [...],
            "duplicate_records_removed": int,
            "invalid_timestamps": int,
            "record_count": int,
            "processed_data": [...]   # only present when data_ready is True
        }
    """
    raw_records: List[Dict[str, Any]] = creator_data.get("raw_data", [])
    original_count = len(raw_records)

    # 1. Schema mapping
    mapped_records = map_dataset(raw_records)

    # 2. Deduplication
    mapped_records, duplicate_count = _dedupe(mapped_records)

    # 3. Timestamp validation
    mapped_records, invalid_timestamp_count = _validate_timestamps(mapped_records)

    # 4. Normalize engagement metrics to numeric types
    numeric_fields = ["likes_count", "comments_count", "shares_count", "saves_count", "reach", "impressions"]
    for record in mapped_records:
        for field in numeric_fields:
            _coerce_numeric(record, field)

    # 5. Feature coverage
    coverage = detect_available_and_missing(mapped_records)

    # 6. Quality score
    quality_score = _calculate_quality_score(
        mapped_records,
        coverage["available_features"],
        duplicate_count,
        invalid_timestamp_count,
        original_count,
    )

    missing_required = [f for f in REQUIRED_FOR_ANALYSIS if f in coverage["missing_features"]]
    data_ready = quality_score >= quality_threshold and not missing_required

    result: Dict[str, Any] = {
        "data_ready": data_ready,
        "quality_score": quality_score,
        "missing_features": coverage["missing_features"],
        "available_features": coverage["available_features"],
        "duplicate_records_removed": duplicate_count,
        "invalid_timestamps": invalid_timestamp_count,
        "record_count": len(mapped_records),
    }

    if data_ready:
        result["processed_data"] = mapped_records

    return result
