"""
Analytics modules: metrics computation, trend detection, and anomaly detection.
"""

from backend.analytics.metrics import calculate_post_metrics, calculate_aggregate_metrics
from backend.analytics.trends import detect_trends, find_best_posting_window
from backend.analytics.anomalies import detect_anomalies

__all__ = [
    "calculate_post_metrics",
    "calculate_aggregate_metrics",
    "detect_trends",
    "find_best_posting_window",
    "detect_anomalies",
]
