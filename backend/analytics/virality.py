"""
backend/analytics/virality.py

Virality Machine Learning & Predictive Analytics Engine.
Evaluates:
1. Hook Strength & Cognitive Triggers (Length, curiosity gap, question/listicle format, power verbs).
2. Content Type & Algorithmic Discovery Affinity (Reel/Carousel/Static vs creator benchmark).
3. Temporal & Peak Window Alignment (Historical best day/hour match).
4. Saveability & Shareability Friction (Actionable CTA, bookmark prompts, value density).
5. Viral Trend Radar Alignment (Overlap with active trending signals).

Outputs:
- virality_score (0-100)
- tier ("Breakout Potential", "High Potential", "Moderate", "Niche / Low")
- predicted_reach_multiplier (e.g. 0.6x to 3.8x)
- predicted_reach_range (min, median, max grounded in creator's history)
- category_scores (hook, format, timing, save_share, trend)
- actionable_recommendations (specific improvements)
"""

from __future__ import annotations
import math
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from backend.analytics.metrics import calculate_post_engagement_rate
from backend.analytics.trends import find_best_posting_window


# High-converting curiosity & psychological hook triggers
CURIOSITY_TRIGGERS = [
    r"\bsecret\b", r"\bsecrets\b", r"\bwhy most\b", r"\bstop doing\b",
    r"\bstop making\b", r"\bmistake\b", r"\bmistakes\b", r"\btruth about\b",
    r"\bthe real reason\b", r"\bnobody is talking about\b", r"\bnobody tells you\b",
    r"\bunpopular opinion\b", r"\bhow i\b", r"\bhow to actually\b",
    r"\bwarning\b", r"\bexposed\b", r"\bhack\b", r"\bhacks\b",
    r"\bblueprint\b", r"\bframework\b", r"\bsteals?\b", r"\bloophole\b",
]

POWER_VERBS = [
    r"\btransform\b", r"\bskyrocket\b", r"\bexplode\b", r"\bscale\b",
    r"\beliminate\b", r"\bmaster\b", r"\bautomate\b", r"\bdestroy\b",
    r"\bguarantee\b", r"\breveal\b", r"\baccelerate\b", r"\bmultiply\b",
]

SAVE_SHARE_PROMPTS = [
    r"\bsave this\b", r"\bsave for later\b", r"\bbookmark\b", r"\bkeep this\b",
    r"\bshare this\b", r"\bshare with\b", r"\bsend this to\b", r"\btag a friend\b",
    r"\btag someone\b", r"\bpass this along\b",
]


class ViralityPredictor:
    """Predictive analytics and ML scoring for Instagram post virality potential."""

    @classmethod
    def evaluate_hook(cls, hook_text: str) -> Tuple[float, str, List[str]]:
        """
        Evaluates hook copy (0-25 points).
        Checks length (5-12 words is optimal), psychological curiosity gap,
        numerical structure, question format, and action verbs.
        """
        recs: List[str] = []
        if not hook_text or not hook_text.strip():
            return 5.0, "Missing hook copy", ["Add a clear, scroll-stopping hook within the first 3 seconds or top caption line."]

        words = hook_text.strip().split()
        word_count = len(words)
        clean_hook = hook_text.lower()
        score = 0.0

        # 1. Length scoring (0-7 pts)
        if 5 <= word_count <= 11:
            score += 7.0
        elif 3 <= word_count <= 15:
            score += 5.0
            if word_count > 11:
                recs.append(f"Shorten hook from {word_count} to 6-9 words for faster mobile scanning.")
        else:
            score += 2.0
            recs.append("Hook length is outside the ideal window (5-11 words); trim excess filler words.")

        # 2. Curiosity gap & pattern interrupt (0-8 pts)
        curiosity_hits = [p for p in CURIOSITY_TRIGGERS if re.search(p, clean_hook)]
        if curiosity_hits:
            score += min(8.0, 5.0 + len(curiosity_hits) * 2.0)
        else:
            recs.append("Incorporate a stronger curiosity gap (e.g., 'The truth about...', 'Stop making this mistake').")

        # 3. Numerical / Listicle structure (0-4 pts)
        has_number = bool(re.search(r"\b\d+\b", clean_hook))
        if has_number:
            score += 4.0
        else:
            recs.append("Adding a specific number (e.g. '3 reasons', '5 tools') increases click-through & retention.")

        # 4. Question or urgency punctuation (0-3 pts)
        if "?" in hook_text or "!" in hook_text:
            score += 3.0
        else:
            score += 1.0

        # 5. Power verbs (0-3 pts)
        power_hits = [v for v in POWER_VERBS if re.search(v, clean_hook)]
        if power_hits:
            score += min(3.0, 1.5 * len(power_hits))

        score = min(25.0, round(score, 1))
        feedback = f"Hook score: {score}/25. Structure is {'compelling' if score >= 18 else 'adequate' if score >= 12 else 'weak'}."
        return score, feedback, recs

    @classmethod
    def evaluate_format(
        cls,
        content_type: str,
        historical_posts: List[Dict[str, Any]]
    ) -> Tuple[float, str, List[str]]:
        """
        Evaluates algorithmic format discovery affinity (0-20 points).
        Reels receive highest organic exploration; Carousels offer high repeat saves.
        Also evaluates alignment with creator's historical best-performing format.
        """
        recs: List[str] = []
        fmt = (content_type or "REEL").upper()
        base_scores = {
            "REEL": 15.0,
            "VIDEO": 14.0,
            "CAROUSEL": 13.0,
            "CAROUSEL_ALBUM": 13.0,
            "IMAGE": 9.0,
            "PHOTO": 9.0,
        }
        score = base_scores.get(fmt, 10.0)

        # Historical affinity check
        format_performance: Dict[str, List[float]] = {}
        for p in historical_posts:
            p_type = (p.get("content_type") or p.get("media_type") or "IMAGE").upper()
            er = p.get("engagement_rate") or calculate_post_engagement_rate(p)
            if er is not None:
                format_performance.setdefault(p_type, []).append(er)

        best_fmt = None
        best_avg_er = -1.0
        for f, ers in format_performance.items():
            if len(ers) >= 2:
                avg = sum(ers) / len(ers)
                if avg > best_avg_er:
                    best_avg_er = avg
                    best_fmt = f

        if best_fmt:
            if fmt == best_fmt:
                score += 5.0
            else:
                score += 2.0
                recs.append(f"Your historical data shows '{best_fmt}' yields highest average engagement ({round(best_avg_er, 2)}%). Consider testing as a {best_fmt}.")
        else:
            score += 3.0  # default historical credit

        score = min(20.0, round(score, 1))
        feedback = f"Format potential: {score}/20 ({fmt})."
        return score, feedback, recs

    @classmethod
    def evaluate_timing(
        cls,
        scheduled_time: Optional[datetime],
        historical_posts: List[Dict[str, Any]]
    ) -> Tuple[float, str, List[str]]:
        """
        Evaluates posting window alignment against creator's peak interaction window (0-20 points).
        """
        recs: List[str] = []
        best_window_str = find_best_posting_window(historical_posts)

        if not scheduled_time:
            recs.append(f"Optimal window for your account: {best_window_str}. Schedule content within this block.")
            return 12.0, f"Unscheduled. Account benchmark: {best_window_str}.", recs

        # Ensure UTC timezone
        dt = scheduled_time if scheduled_time.tzinfo else scheduled_time.replace(tzinfo=timezone.utc)
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        post_day = day_names[dt.weekday()]
        post_hour = dt.hour

        score = 10.0
        if "Insufficient" not in best_window_str:
            # Parse expected day and hours: e.g. "Wednesday 18:00 - 21:00 UTC"
            parts = best_window_str.split()
            if len(parts) >= 4:
                target_day = parts[0]
                try:
                    start_h = int(parts[1].split(":")[0])
                    end_h = int(parts[3].split(":")[0])
                    if post_day == target_day and start_h <= post_hour < end_h:
                        score = 20.0
                    elif post_day == target_day or abs(post_hour - start_h) <= 2:
                        score = 15.0
                    else:
                        score = 8.0
                        recs.append(f"Post is scheduled for {post_day} {post_hour:02d}:00 UTC. Your peak engagement window is {best_window_str}.")
                except (ValueError, IndexError):
                    score = 12.0
        else:
            # Platform general peaks: 12:00-14:00 or 18:00-21:00
            if (12 <= post_hour <= 14) or (18 <= post_hour <= 21):
                score = 16.0
            else:
                score = 11.0
                recs.append("Consider scheduling between 18:00 - 21:00 UTC to capture maximum active platform traffic.")

        score = min(20.0, round(score, 1))
        feedback = f"Timing score: {score}/20 (Scheduled: {post_day} {post_hour:02d}:00 UTC)."
        return score, feedback, recs

    @classmethod
    def evaluate_save_share_cta(cls, caption: str) -> Tuple[float, str, List[str]]:
        """
        Evaluates saveability, shareability cues, and caption value density (0-20 points).
        """
        recs: List[str] = []
        if not caption or not caption.strip():
            recs.append("Add a detailed value caption with a clear Call to Action ('Save this for later').")
            return 4.0, "Empty or minimal caption", recs

        clean_cap = caption.lower()
        score = 0.0

        # 1. Save & Share triggers (0-10 pts)
        save_hits = [p for p in SAVE_SHARE_PROMPTS if re.search(p, clean_cap)]
        if save_hits:
            score += min(10.0, 6.0 + len(save_hits) * 2.0)
        else:
            score += 2.0
            recs.append("Add an explicit Save/Share call to action (e.g., 'Save this so you can reference it when creating your next Reel').")

        # 2. Formatting & Value density (0-6 pts)
        lines = caption.strip().split("\n")
        has_bullets = any(line.strip().startswith(("-", "•", "1.", "2.", "👉", "✅", "🔥")) for line in lines)
        if has_bullets or len(lines) >= 4:
            score += 6.0
        else:
            score += 2.0
            recs.append("Structure caption with bullet points or step-by-step formatting to increase reading time.")

        # 3. Caption length sweet spot (0-4 pts)
        char_len = len(caption.strip())
        if 150 <= char_len <= 1200:
            score += 4.0
        else:
            score += 2.0

        score = min(20.0, round(score, 1))
        feedback = f"Save/Share friction: {score}/20."
        return score, feedback, recs

    @classmethod
    def evaluate_trend_alignment(
        cls,
        text_corpus: str,
        active_trends: List[str]
    ) -> Tuple[float, str, List[str]]:
        """
        Evaluates keyword alignment with active trending radar topics (0-15 points).
        """
        recs: List[str] = []
        if not active_trends:
            return 8.0, "No active trend signals available in database.", recs

        clean_corpus = text_corpus.lower()
        matched_trends = []
        for trend in active_trends:
            # Check multi-word or single word overlap
            trend_clean = trend.lower().strip()
            if len(trend_clean) >= 3 and trend_clean in clean_corpus:
                matched_trends.append(trend)

        if matched_trends:
            score = min(15.0, 7.0 + len(matched_trends) * 4.0)
            feedback = f"Trend alignment: {score}/15 (Matches: {', '.join(matched_trends[:3])})."
        else:
            score = 6.0
            recs.append(f"Consider integrating rising niche signals (e.g., '{active_trends[0]}') to leverage algorithmic explore velocity.")
            feedback = "Trend alignment: 6/15 (No active trend overlap detected)."

        return score, feedback, recs

    @classmethod
    def predict(
        cls,
        hook: str,
        caption: str,
        content_type: str = "REEL",
        scheduled_time: Optional[datetime] = None,
        hashtags: Optional[List[str]] = None,
        historical_posts: Optional[List[Dict[str, Any]]] = None,
        active_trends: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Executes end-to-end multi-factor virality prediction.
        Returns full score breakdown, tier, reach multiplier, and actionable suggestions.
        """
        historical_posts = historical_posts or []
        active_trends = active_trends or []
        hashtags = hashtags or []

        # Derive hook from caption if omitted
        effective_hook = hook.strip() if hook and hook.strip() else ""
        if not effective_hook and caption:
            effective_hook = caption.strip().split("\n")[0][:120]

        combined_text = f"{effective_hook} {caption} {' '.join(hashtags)}"

        # Compute factor scores
        hook_score, hook_fb, hook_recs = cls.evaluate_hook(effective_hook)
        fmt_score, fmt_fb, fmt_recs = cls.evaluate_format(content_type, historical_posts)
        timing_score, timing_fb, timing_recs = cls.evaluate_timing(scheduled_time, historical_posts)
        cta_score, cta_fb, cta_recs = cls.evaluate_save_share_cta(caption)
        trend_score, trend_fb, trend_recs = cls.evaluate_trend_alignment(combined_text, active_trends)

        total_score = round(hook_score + fmt_score + timing_score + cta_score + trend_score)
        total_score = max(5, min(100, total_score))

        # Classify Tier
        if total_score >= 85:
            tier = "Breakout Potential 🚀"
            multiplier_base = 2.4
        elif total_score >= 70:
            tier = "High Potential 🔥"
            multiplier_base = 1.6
        elif total_score >= 50:
            tier = "Moderate Reach 📈"
            multiplier_base = 1.0
        else:
            tier = "Niche / Low Velocity ⚠️"
            multiplier_base = 0.65

        # Precise multiplier scaling
        reach_multiplier = round(0.5 + (total_score / 100.0) * 2.3, 2)

        # Baseline reach grounded in creator's actual historical reach
        reach_values = [p.get("reach") for p in historical_posts if p.get("reach") and p.get("reach") > 0]
        if reach_values:
            reach_values.sort()
            median_reach = reach_values[len(reach_values) // 2]
            min_reach = max(10, int(median_reach * (reach_multiplier * 0.65)))
            expected_median_reach = int(median_reach * reach_multiplier)
            max_reach = int(median_reach * (reach_multiplier * 1.65))
        else:
            # Fallback benchmark
            expected_median_reach = int(1000 * reach_multiplier)
            min_reach = int(expected_median_reach * 0.6)
            max_reach = int(expected_median_reach * 1.8)

        # Compile consolidated recommendations
        all_recs = hook_recs + fmt_recs + timing_recs + cta_recs + trend_recs

        return {
            "virality_score": total_score,
            "tier": tier,
            "predicted_reach_multiplier": reach_multiplier,
            "predicted_reach_range": {
                "min_reach": min_reach,
                "median_reach": expected_median_reach,
                "max_reach": max_reach,
            },
            "category_scores": {
                "hook_strength": {"score": hook_score, "max": 25, "feedback": hook_fb},
                "format_affinity": {"score": fmt_score, "max": 20, "feedback": fmt_fb},
                "timing_alignment": {"score": timing_score, "max": 20, "feedback": timing_fb},
                "save_share_potential": {"score": cta_score, "max": 20, "feedback": cta_fb},
                "trend_alignment": {"score": trend_score, "max": 15, "feedback": trend_fb},
            },
            "actionable_recommendations": all_recs[:5],  # top 5 most impactful
        }
