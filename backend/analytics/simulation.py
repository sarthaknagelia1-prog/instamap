"""
backend/analytics/simulation.py

Content & Growth Simulation Layer.
Provides:
1. Monte Carlo Growth Simulation (30, 60, 90-day trajectory modeling across Baseline, Recommended, and Aggressive scenarios).
2. What-If Single Post Reach Simulation (500-draw distribution modeling, confidence intervals, breakout probability).
"""

from __future__ import annotations
import math
import random
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from backend.analytics.metrics import calculate_post_engagement_rate
from backend.analytics.virality import ViralityPredictor


class GrowthSimulator:
    """Simulates creator growth trajectories and content performance under multiple strategic scenarios."""

    @staticmethod
    def _extract_historical_stats(posts: List[Dict[str, Any]]) -> Dict[str, float]:
        """Extracts mean, std dev, median reach, and average posts/week from history."""
        if not posts:
            return {
                "mean_reach": 1000.0,
                "median_reach": 850.0,
                "std_reach": 350.0,
                "avg_er": 4.5,
                "posts_per_week": 3.0,
            }

        reaches = [float(p.get("reach") or 0) for p in posts if p.get("reach") and p.get("reach") > 0]
        ers = [
            float(p.get("engagement_rate") or calculate_post_engagement_rate(p) or 0)
            for p in posts
        ]
        ers = [e for e in ers if e > 0]

        if not reaches:
            reaches = [1000.0]
        reaches.sort()

        n = len(reaches)
        mean_reach = sum(reaches) / n
        median_reach = reaches[n // 2]
        variance = sum((x - mean_reach) ** 2 for x in reaches) / max(1, n - 1)
        std_reach = math.sqrt(variance) if variance > 0 else mean_reach * 0.35

        avg_er = (sum(ers) / len(ers)) if ers else 4.0

        # Estimate posts per week from date span if available
        dts = []
        for p in posts:
            val = p.get("timestamp")
            if val:
                try:
                    dt = val if isinstance(val, datetime) else datetime.fromisoformat(str(val).replace("Z", "+00:00"))
                    dts.append(dt)
                except Exception:
                    pass

        posts_per_week = 3.0
        if len(dts) >= 2:
            dts.sort()
            span_days = max(7, (dts[-1] - dts[0]).days)
            posts_per_week = max(1.0, min(14.0, (len(dts) / span_days) * 7.0))

        return {
            "mean_reach": max(100.0, mean_reach),
            "median_reach": max(80.0, median_reach),
            "std_reach": max(50.0, std_reach),
            "avg_er": max(0.5, avg_er),
            "posts_per_week": round(posts_per_week, 1),
        }

    @classmethod
    def simulate_growth(
        cls,
        historical_posts: List[Dict[str, Any]],
        days: int = 60,
        iterations: int = 100,
        seed: Optional[int] = 42,
    ) -> Dict[str, Any]:
        """
        Runs Monte Carlo growth simulations across:
        1. Baseline (Current trajectory)
        2. Recommended (60/30/10 format allocation, peak windows, +25% reach, optimized retention)
        3. Aggressive (1.8x cadence, trend radar leverage, +50% reach, higher variance)
        """
        if seed is not None:
            random.seed(seed)

        days = max(14, min(180, days))
        stats = cls._extract_historical_stats(historical_posts)

        base_weekly_cadence = stats["posts_per_week"]
        rec_weekly_cadence = max(3.5, base_weekly_cadence * 1.25)
        agg_weekly_cadence = min(14.0, max(5.0, base_weekly_cadence * 1.8))

        # Daily posting probabilities
        p_base = base_weekly_cadence / 7.0
        p_rec = rec_weekly_cadence / 7.0
        p_agg = agg_weekly_cadence / 7.0

        # Scenario reach parameters: (mean_multiplier, std_multiplier, er_multiplier, follower_conversion_rate)
        scenarios = {
            "baseline": (1.0, 1.0, 1.0, 0.008),
            "recommended": (1.30, 0.85, 1.35, 0.012),
            "aggressive": (1.60, 1.25, 1.45, 0.015),
        }

        # Track daily cumulative distributions across iterations
        # simulation_results[scenario][day] = list of cumulative reach across iterations
        scenario_daily_reach: Dict[str, List[List[float]]] = {s: [[] for _ in range(days)] for s in scenarios}
        scenario_daily_followers: Dict[str, List[List[float]]] = {s: [[] for _ in range(days)] for s in scenarios}
        scenario_total_posts: Dict[str, List[int]] = {s: [] for s in scenarios}

        log_mu = math.log(max(10.0, stats["median_reach"]))
        log_sigma = 0.5  # standard log-normal shape for social media distributions

        for _ in range(iterations):
            for sc_name, (mean_mult, std_mult, er_mult, conv_rate) in scenarios.items():
                p_day = p_base if sc_name == "baseline" else (p_rec if sc_name == "recommended" else p_agg)
                cum_reach = 0.0
                cum_followers = 0.0
                post_count = 0

                for day in range(days):
                    if random.random() < p_day:
                        post_count += 1
                        # Draw log-normal post reach
                        draw = math.exp(random.gauss(log_mu, log_sigma * std_mult)) * mean_mult
                        interactions = draw * (stats["avg_er"] / 100.0) * er_mult
                        followers_gained = interactions * conv_rate
                        cum_reach += draw
                        cum_followers += followers_gained

                    scenario_daily_reach[sc_name][day].append(cum_reach)
                    scenario_daily_followers[sc_name][day].append(cum_followers)

                scenario_total_posts[sc_name].append(post_count)

        # Build timeline series with percentiles
        start_date = datetime.now(timezone.utc)
        timeline = []

        def get_percentile(vals: List[float], p: float) -> float:
            s_vals = sorted(vals)
            idx = int(len(s_vals) * p)
            return s_vals[min(idx, len(s_vals) - 1)]

        for day in range(days):
            cur_date = start_date + timedelta(days=day + 1)
            date_str = cur_date.strftime("%Y-%m-%d")

            b_reach = get_percentile(scenario_daily_reach["baseline"][day], 0.5)
            r_reach = get_percentile(scenario_daily_reach["recommended"][day], 0.5)
            a_reach = get_percentile(scenario_daily_reach["aggressive"][day], 0.5)

            r_lower = get_percentile(scenario_daily_reach["recommended"][day], 0.1)
            r_upper = get_percentile(scenario_daily_reach["recommended"][day], 0.9)

            b_foll = get_percentile(scenario_daily_followers["baseline"][day], 0.5)
            r_foll = get_percentile(scenario_daily_followers["recommended"][day], 0.5)
            a_foll = get_percentile(scenario_daily_followers["aggressive"][day], 0.5)

            timeline.append({
                "day": day + 1,
                "date": date_str,
                "baseline_reach": round(b_reach),
                "recommended_reach": round(r_reach),
                "aggressive_reach": round(a_reach),
                "recommended_lower": round(r_lower),
                "recommended_upper": round(r_upper),
                "baseline_followers": round(b_foll),
                "recommended_followers": round(r_foll),
                "aggressive_followers": round(a_foll),
            })

        # Calculate final comparison summaries
        final_day = days - 1
        b_final_reach = timeline[final_day]["baseline_reach"]
        r_final_reach = timeline[final_day]["recommended_reach"]
        a_final_reach = timeline[final_day]["aggressive_reach"]

        b_final_foll = timeline[final_day]["baseline_followers"]
        r_final_foll = timeline[final_day]["recommended_followers"]
        a_final_foll = timeline[final_day]["aggressive_followers"]

        reach_lift_pct = round(((r_final_reach - b_final_reach) / max(1, b_final_reach)) * 100.0, 1)
        foll_lift_pct = round(((r_final_foll - b_final_foll) / max(1, b_final_foll)) * 100.0, 1)

        summary = {
            "baseline": {
                "projected_posts": round(sum(scenario_total_posts["baseline"]) / iterations),
                "projected_reach": b_final_reach,
                "projected_followers": b_final_foll,
                "cadence_posts_per_week": base_weekly_cadence,
            },
            "recommended": {
                "projected_posts": round(sum(scenario_total_posts["recommended"]) / iterations),
                "projected_reach": r_final_reach,
                "projected_followers": r_final_foll,
                "cadence_posts_per_week": round(rec_weekly_cadence, 1),
                "reach_lift_vs_baseline_pct": reach_lift_pct,
                "follower_lift_vs_baseline_pct": foll_lift_pct,
            },
            "aggressive": {
                "projected_posts": round(sum(scenario_total_posts["aggressive"]) / iterations),
                "projected_reach": a_final_reach,
                "projected_followers": a_final_foll,
                "cadence_posts_per_week": round(agg_weekly_cadence, 1),
            },
        }

        takeaways = [
            f"Adopting the Recommended Strategy over {days} days is projected to generate +{reach_lift_pct}% cumulative reach ({r_final_reach:,} vs {b_final_reach:,}).",
            f"Optimized format allocation and saveable CTAs boost projected follower conversions by +{foll_lift_pct}%.",
            f"The 80% confidence interval for recommended strategy ranges from {timeline[final_day]['recommended_lower']:,} to {timeline[final_day]['recommended_upper']:,} reach.",
        ]

        return {
            "simulation_days": days,
            "iterations": iterations,
            "baseline_stats": stats,
            "summary": summary,
            "strategic_takeaways": takeaways,
            "timeline": timeline,
        }

    @classmethod
    def simulate_post(
        cls,
        hook: str,
        caption: str,
        content_type: str = "REEL",
        scheduled_time: Optional[datetime] = None,
        hashtags: Optional[List[str]] = None,
        historical_posts: Optional[List[Dict[str, Any]]] = None,
        active_trends: Optional[List[str]] = None,
        draws: int = 500,
        seed: Optional[int] = 42,
    ) -> Dict[str, Any]:
        """
        Simulates individual post reach distribution via 500 Monte Carlo draws.
        Evaluates virality multiplier, percentiles (p10, p50, p90, p99),
        breakout probability, and distribution histogram bins.
        """
        if seed is not None:
            random.seed(seed)

        historical_posts = historical_posts or []
        stats = cls._extract_historical_stats(historical_posts)

        # Run Virality Predictor
        virality_res = ViralityPredictor.predict(
            hook=hook,
            caption=caption,
            content_type=content_type,
            scheduled_time=scheduled_time,
            hashtags=hashtags,
            historical_posts=historical_posts,
            active_trends=active_trends,
        )

        reach_mult = virality_res["predicted_reach_multiplier"]
        median_base = stats["median_reach"]

        log_mu = math.log(max(10.0, median_base * reach_mult))
        log_sigma = 0.45

        simulated_reaches = []
        for _ in range(draws):
            reach_draw = math.exp(random.gauss(log_mu, log_sigma))
            simulated_reaches.append(round(reach_draw))

        simulated_reaches.sort()

        def pct(p: float) -> int:
            idx = int(len(simulated_reaches) * p)
            return simulated_reaches[min(idx, len(simulated_reaches) - 1)]

        p10 = pct(0.10)
        p25 = pct(0.25)
        p50 = pct(0.50)
        p75 = pct(0.75)
        p90 = pct(0.90)
        p99 = pct(0.99)

        # Breakout probability: chance of exceeding creator's top 10% historical reach
        hist_reaches = [float(p.get("reach") or 0) for p in historical_posts if p.get("reach")]
        if hist_reaches:
            hist_reaches.sort()
            hist_90th = hist_reaches[int(len(hist_reaches) * 0.90)]
        else:
            hist_90th = median_base * 1.5

        breakouts = sum(1 for r in simulated_reaches if r > hist_90th)
        prob_breakout_pct = round((breakouts / draws) * 100.0, 1)

        # Compute histogram bins for visualization
        min_val = p10 * 0.8
        max_val = p99 * 1.1
        bin_count = 10
        bin_width = max(1.0, (max_val - min_val) / bin_count)
        bins = []

        for b in range(bin_count):
            b_start = min_val + b * bin_width
            b_end = b_start + bin_width
            count = sum(1 for r in simulated_reaches if b_start <= r < b_end)
            bins.append({
                "range_label": f"{int(b_start):,} - {int(b_end):,}",
                "min": round(b_start),
                "max": round(b_end),
                "frequency": count,
                "percentage": round((count / draws) * 100.0, 1),
            })

        return {
            "virality_evaluation": virality_res,
            "simulation_stats": {
                "draws": draws,
                "historical_median_reach": round(median_base),
                "historical_breakout_threshold": round(hist_90th),
                "percentiles": {
                    "p10_conservative": p10,
                    "p25_moderate_low": p25,
                    "p50_expected_median": p50,
                    "p75_moderate_high": p75,
                    "p90_viral_upside": p90,
                    "p99_super_viral": p99,
                },
                "prob_breakout_pct": prob_breakout_pct,
            },
            "distribution_bins": bins,
        }
