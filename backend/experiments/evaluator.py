"""
backend/experiments/evaluator.py

Statistical Significance Evaluator for A/B Experiments.
Implements Welch's two-sample t-test to compare creator content variants
(e.g., hooks, formats, schedules) without assuming equal variances.
"""

from __future__ import annotations
import math
from typing import Any, Dict, List, Optional


def _mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _variance(values: List[float], mean_val: float) -> float:
    if len(values) < 2:
        return 0.0
    return sum((x - mean_val) ** 2 for x in values) / (len(values) - 1)


def _student_t_p_value(t: float, df: float) -> float:
    """
    Computes two-tailed p-value for Student's t-statistic using
    the Abramowitz & Stegun transformation to standard normal.
    """
    if df <= 0 or math.isnan(t):
        return 1.0
    if abs(t) < 1e-9:
        return 1.0

    # Normal approximation mapping t and df to z-score
    z = abs(t) * (1.0 - 1.0 / (4.0 * df)) / math.sqrt(1.0 + (t * t) / (2.0 * df))
    p = math.erfc(z / math.sqrt(2.0))
    return min(1.0, max(0.0, p))


def evaluate_experiment_metrics(
    variant_a_values: List[float],
    variant_b_values: List[float],
    alpha: float = 0.05,
    min_sample_size: int = 3,
) -> Dict[str, Any]:
    """
    Evaluates whether Variant B is statistically significantly different from Variant A.

    Parameters:
        variant_a_values: Metric values for control / Variant A (e.g., engagement rates)
        variant_b_values: Metric values for treatment / Variant B
        alpha: Significance threshold (default 0.05 for 95% confidence)
        min_sample_size: Minimum posts required per variant

    Returns structured evaluation dict.
    """
    n_a = len(variant_a_values)
    n_b = len(variant_b_values)

    if n_a < min_sample_size or n_b < min_sample_size:
        return {
            "status": "completed_inconclusive",
            "is_significant": False,
            "winner": None,
            "p_value": 1.0,
            "t_statistic": 0.0,
            "degrees_of_freedom": 0.0,
            "sample_size_a": n_a,
            "sample_size_b": n_b,
            "mean_a": round(_mean(variant_a_values), 4),
            "mean_b": round(_mean(variant_b_values), 4),
            "relative_difference_pct": 0.0,
            "confidence_pct": 0.0,
            "summary": f"Sample size too small ({n_a} vs {n_b}). Need at least {min_sample_size} posts per variant.",
        }

    mean_a = _mean(variant_a_values)
    mean_b = _mean(variant_b_values)
    var_a = _variance(variant_a_values, mean_a)
    var_b = _variance(variant_b_values, mean_b)

    # Standard error of difference
    se_a = var_a / n_a
    se_b = var_b / n_b
    se_diff = math.sqrt(se_a + se_b)

    if se_diff < 1e-9:
        diff = mean_b - mean_a
        is_identical = abs(diff) < 1e-9
        return {
            "status": "completed_inconclusive" if is_identical else "completed_conclusive",
            "is_significant": not is_identical,
            "winner": "variant_b" if diff > 0 else ("variant_a" if diff < 0 else None),
            "p_value": 0.0 if not is_identical else 1.0,
            "t_statistic": 99.0 if diff > 0 else -99.0,
            "degrees_of_freedom": float(n_a + n_b - 2),
            "sample_size_a": n_a,
            "sample_size_b": n_b,
            "mean_a": round(mean_a, 4),
            "mean_b": round(mean_b, 4),
            "relative_difference_pct": round(((mean_b - mean_a) / mean_a) * 100, 2) if mean_a > 0 else 0.0,
            "confidence_pct": 100.0 if not is_identical else 0.0,
            "summary": "Identical variants with zero variance." if is_identical else "Zero variance detected with strict separation.",
        }

    # Welch-Satterthwaite degrees of freedom
    numerator = (se_a + se_b) ** 2
    denom_a = (se_a ** 2) / (n_a - 1) if n_a > 1 else 1e-9
    denom_b = (se_b ** 2) / (n_b - 1) if n_b > 1 else 1e-9
    df = numerator / (denom_a + denom_b)

    # t-statistic and two-tailed p-value
    t_stat = (mean_b - mean_a) / se_diff
    p_val = _student_t_p_value(t_stat, df)

    diff = mean_b - mean_a
    rel_diff_pct = round((diff / mean_a) * 100, 2) if mean_a > 0 else round(diff * 100, 2)
    is_significant = (p_val < alpha)

    winner = None
    if is_significant:
        winner = "variant_b" if mean_b > mean_a else "variant_a"

    status = "completed_conclusive" if is_significant else "completed_inconclusive"
    confidence_pct = round((1.0 - p_val) * 100, 2)

    if is_significant:
        summary = (
            f"Statistically conclusive result ({confidence_pct:.1f}% confidence, p={p_val:.4f}). "
            f"Winner: {winner.upper()} with a {abs(rel_diff_pct):.1f}% performance advantage."
        )
    else:
        summary = (
            f"Inconclusive result (p={p_val:.4f} >= {alpha}). "
            f"No statistically significant difference detected between Variant A ({mean_a:.2f}) and Variant B ({mean_b:.2f})."
        )

    return {
        "status": status,
        "is_significant": is_significant,
        "winner": winner,
        "p_value": round(p_val, 4),
        "t_statistic": round(t_stat, 4),
        "degrees_of_freedom": round(df, 2),
        "sample_size_a": n_a,
        "sample_size_b": n_b,
        "mean_a": round(mean_a, 4),
        "mean_b": round(mean_b, 4),
        "relative_difference_pct": rel_diff_pct,
        "confidence_pct": confidence_pct,
        "summary": summary,
    }
