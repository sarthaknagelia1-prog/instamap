"""
backend/data/adapters/trend_sniffing_adapter.py

Trend Sniffing Adapter:
Discovers rising topics, debates, and queries across external platforms
(Reddit public JSON, Google Trends daily RSS, and curated niche radars)
with zero paid API keys, and synthesizes high-retention Instagram Hooks.
"""

from __future__ import annotations
import math
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
import httpx
from sqlalchemy.orm import Session

from backend.data.adapters.base_adapter import BaseAdapter
from backend.database.models import TrendingSignal, utcnow

# Niche to Subreddit Mapping
NICHE_SUBREDDITS: Dict[str, List[str]] = {
    "Tech & AI": ["artificial", "technology", "OpenAI", "singularity"],
    "Fitness & Health": ["fitness", "bodyweightfitness", "nutrition"],
    "Personal Finance": ["personalfinance", "investing", "financialindependence"],
    "Business & Marketing": ["entrepreneur", "smallbusiness", "marketing"],
    "Design & UI/UX": ["web_design", "graphic_design", "userexperience"],
    "Gaming": ["gaming", "pcgaming", "games"],
    "Productivity": ["productivity", "getdisciplined"],
    "Fashion & Beauty": ["malefashionadvice", "femalefashionadvice", "skincareaddiction"],
    "Food & Cooking": ["cooking", "recipes", "eatcheapandhealthy"],
    "Education & Career": ["careerguidance", "cscareerquestions", "jobs"],
}

# Curated High-Velocity Evergreen & Seasonal Radar (100% Offline Reliable)
CURATED_RADAR: Dict[str, List[Dict[str, Any]]] = {
    "Tech & AI": [
        {
            "topic": "Open-Source AI Models vs Proprietary APIs: Speed & Cost Reality",
            "velocity_score": 94.0,
            "suggested_hook": "Stop paying for AI API credits before you test this local workflow.",
            "suggested_angle": "Benchmark comparison showing a 10x cost reduction using distilled open weights.",
            "recommended_format": "reel",
        },
        {
            "topic": "AI Coding Agents Replacing Boilerplate Dev Workflows",
            "velocity_score": 88.5,
            "suggested_hook": "Most developers are using AI code assistants completely backwards.",
            "suggested_angle": "Step-by-step breakdown of prompt-to-production workflows.",
            "recommended_format": "carousel",
        },
        {
            "topic": "Agentic Reasoning Benchmarks: What Real-World Benchmarks Actually Reveal",
            "velocity_score": 82.0,
            "suggested_hook": "The latest AI reasoning benchmark numbers have one massive flaw.",
            "suggested_angle": "Visual flowchart explaining where benchmark leakage happens.",
            "recommended_format": "carousel",
        },
    ],
    "Fitness & Health": [
        {
            "topic": "High-Volume Hypertrophy vs Rest-Pause Density Training",
            "velocity_score": 91.0,
            "suggested_hook": "Why spending 2 hours in the gym is actually sabotaging your muscle growth.",
            "suggested_angle": "Scientific comparison of mechanical tension vs training fatigue.",
            "recommended_format": "reel",
        },
        {
            "topic": "Micro-Habits for Sleep Architecture & Deep Recovery",
            "velocity_score": 85.0,
            "suggested_hook": "The 3 sleep mistakes keeping your cortisol permanently elevated.",
            "suggested_angle": "5-slide evening wind-down protocol with checklist.",
            "recommended_format": "carousel",
        },
    ],
    "Personal Finance": [
        {
            "topic": "Index Fund DCA vs High-Yield Fixed Income in Shifting Rate Climates",
            "velocity_score": 92.5,
            "suggested_hook": "If you have cash sitting in a standard savings account, watch this.",
            "suggested_angle": "Clear comparison chart of purchasing power erosion vs simple index allocations.",
            "recommended_format": "carousel",
        },
        {
            "topic": "Automated Budget Splitting: The 50/30/20 Rule Frictionless Setup",
            "velocity_score": 84.0,
            "suggested_hook": "Stop tracking expenses manually—do this automated banking setup instead.",
            "suggested_angle": "Visual diagram showing sub-account money routing on payday.",
            "recommended_format": "reel",
        },
    ],
    "Business & Marketing": [
        {
            "topic": "Founder-Led Organic Distribution vs Paid Customer Acquisition Costs",
            "velocity_score": 93.0,
            "suggested_hook": "Paid ads are getting too expensive. Here is how founders are getting customers for free.",
            "suggested_angle": "Case study of organic distribution mechanics with actionable playbook.",
            "recommended_format": "reel",
        },
        {
            "topic": "Offer Positioning: Turning Commodity Services into High-Ticket Retainers",
            "velocity_score": 86.0,
            "suggested_hook": "Why you are struggling to charge premium pricing for your work.",
            "suggested_angle": "The 4-part value equation flowchart for service businesses.",
            "recommended_format": "carousel",
        },
    ],
}


NICHE_ALIASES: Dict[str, List[str]] = {
    "Tech & AI": ["tech", "ai", "artificial intelligence", "coding", "software", "developer", "machine learning"],
    "Fitness & Health": ["fitness", "health", "gym", "workout", "bodybuilding", "nutrition", "diet"],
    "Personal Finance": ["finance", "investing", "crypto", "money", "stocks", "stock", "wealth", "budget"],
    "Business & Marketing": ["business", "marketing", "entrepreneur", "startup", "sales", "ecommerce"],
    "Design & UI/UX": ["design", "ui", "ux", "graphic", "web design"],
    "Gaming": ["gaming", "gamer", "games", "esports", "pc gaming"],
    "Productivity": ["productivity", "habits", "discipline", "focus", "time management"],
    "Fashion & Beauty": ["fashion", "beauty", "skincare", "style", "outfit"],
    "Food & Cooking": ["food", "cooking", "recipes", "baking", "culinary"],
    "Education & Career": ["education", "career", "jobs", "college", "interview", "resume"],
}


def _match_niche_key(niche: Optional[str]) -> str:
    """Fuzzy matches input niche string to canonical niche key."""
    if not niche:
        return "Tech & AI"
    low = niche.lower()

    # First check comprehensive niche aliases
    for key, aliases in NICHE_ALIASES.items():
        if any(alias in low for alias in aliases):
            return key

    # Fallback to token matching on canonical keys
    for key in NICHE_SUBREDDITS:
        tokens = [part.strip().lower() for part in key.replace("&", " ").split()]
        if any(token in low for token in tokens if len(token) > 1):
            return key
    return "Tech & AI"


def synthesize_instagram_angle(topic: str, niche: str, velocity_score: float) -> Dict[str, Any]:
    """
    Transforms any raw trend headline into an Instagram-native viral hook,
    narrative angle, and recommended content format.
    """
    clean_topic = topic.strip()
    words = [w.strip(".,:;!?") for w in clean_topic.lower().split()]
    is_comparison = any(w in words for w in ["vs", "vs.", "or", "difference", "compare", "better"]) or " vs " in clean_topic.lower()
    is_how_to = any(w in clean_topic.lower() for w in ["how to", "guide", "setup", "tips", "tutorial"])

    if is_comparison:
        hook = f"The debate is settled: here is the real truth about {clean_topic}."
        angle = f"High-contrast visual comparison breaking down trade-offs, pricing, and practical results."
        format_type = "carousel"
    elif is_how_to or "mistake" in clean_topic.lower():
        hook = f"Stop doing this with {clean_topic} if you want actual results."
        angle = f"Actionable 5-step framework eliminating common pitfalls."
        format_type = "carousel"
    else:
        hook = f"Everyone in {niche} is talking about this—here is what you need to know in 30 seconds."
        angle = f"Fast-paced contrarian breakdown with immediate tactical takeaway."
        format_type = "reel"

    return {
        "suggested_hook": hook,
        "suggested_angle": angle,
        "recommended_format": format_type,
    }


class TrendSniffingAdapter(BaseAdapter):
    """
    Multi-source trend sniffer that harvests rising topics from public Reddit communities,
    Google Trends RSS, and curated radars, producing scored Instagram content opportunities.
    """

    source_name: str = "trend_sniffer"

    def __init__(self, timeout: float = 3.0):
        self.timeout = timeout
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) InstagramGrowthEngine/1.0"

    def fetch_reddit_trends(self, niche: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Fetches top rising/hot discussions from niche subreddits via public JSON."""
        matched_niche = _match_niche_key(niche)
        subreddits = NICHE_SUBREDDITS.get(matched_niche, ["technology"])
        results: List[Dict[str, Any]] = []

        headers = {"User-Agent": self.user_agent}

        for sub in subreddits[:2]:  # Check top 2 subreddits
            url = f"https://www.reddit.com/r/{sub}/hot.json?limit={limit + 2}"
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.get(url, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        posts = data.get("data", {}).get("children", [])
                        for p in posts:
                            post_data = p.get("data", {})
                            if post_data.get("stickied"):
                                continue

                            title = post_data.get("title", "").strip()
                            score = post_data.get("score", 0)
                            num_comments = post_data.get("num_comments", 0)

                            # Calculate velocity score (0 to 100)
                            vel = min(98.0, max(50.0, (score / 40.0) + (num_comments / 10.0)))
                            angle_meta = synthesize_instagram_angle(title, matched_niche, vel)

                            results.append({
                                "topic": title,
                                "source": f"reddit/r/{sub}",
                                "velocity_score": round(vel, 1),
                                "suggested_hook": angle_meta["suggested_hook"],
                                "suggested_angle": angle_meta["suggested_angle"],
                                "recommended_format": angle_meta["recommended_format"],
                                "metadata": {
                                    "subreddit": sub,
                                    "upvotes": score,
                                    "comments": num_comments,
                                    "url": f"https://reddit.com{post_data.get('permalink', '')}",
                                },
                            })
            except Exception:
                # Network fail or rate limit: continue silently
                continue

        return results

    def fetch_google_trends(self, geo: str = "US", limit: int = 5) -> List[Dict[str, Any]]:
        """Fetches real-time search volume surges from public Google Trends daily RSS."""
        url = f"https://trends.google.com/trending/rss?geo={geo}"
        headers = {"User-Agent": self.user_agent}
        results: List[Dict[str, Any]] = []

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(url, headers=headers)
                if resp.status_code == 200:
                    root = ET.fromstring(resp.text)
                    items = root.findall("./channel/item")
                    for item in items[:limit]:
                        title = item.findtext("title") or ""
                        approx_traffic = item.findtext("{https://trends.google.com/trending/rss}approx_traffic") or "10K+"
                        news_title = item.findtext("{https://trends.google.com/trending/rss}news_item/{https://trends.google.com/trending/rss}news_item_title") or title

                        vel = 90.0 if "100K+" in approx_traffic or "500K+" in approx_traffic else 78.0
                        angle_meta = synthesize_instagram_angle(news_title, "General", vel)

                        results.append({
                            "topic": news_title,
                            "source": "google_trends_rss",
                            "velocity_score": round(vel, 1),
                            "suggested_hook": angle_meta["suggested_hook"],
                            "suggested_angle": angle_meta["suggested_angle"],
                            "recommended_format": angle_meta["recommended_format"],
                            "metadata": {"approx_traffic": approx_traffic},
                        })
        except Exception:
            pass

        return results

    def sniff(
        self,
        niche: str = "Tech & AI",
        limit: int = 5,
        use_network: bool = True,
        db: Optional[Session] = None,
    ) -> List[Dict[str, Any]]:
        """
        Coordinates multi-source trend sniffing.
        Returns ranked and scored trending opportunities with fallback to curated radar.
        """
        matched_niche = _match_niche_key(niche)
        gathered: List[Dict[str, Any]] = []

        if use_network:
            reddit_items = self.fetch_reddit_trends(matched_niche, limit=limit)
            gathered.extend(reddit_items)

        # Fallback to Curated Radar if network returned insufficient results
        if len(gathered) < limit:
            radar_items = CURATED_RADAR.get(matched_niche, CURATED_RADAR["Tech & AI"])
            for item in radar_items:
                gathered.append({
                    "topic": item["topic"],
                    "source": "curated_radar",
                    "velocity_score": item["velocity_score"],
                    "suggested_hook": item["suggested_hook"],
                    "suggested_angle": item["suggested_angle"],
                    "recommended_format": item["recommended_format"],
                    "metadata": {"niche": matched_niche, "status": "curated_evergreen"},
                })

        # Deduplicate by topic title
        seen = set()
        unique_results = []
        for g in gathered:
            k = g["topic"].lower().strip()
            if k not in seen:
                seen.add(k)
                unique_results.append(g)

        # Sort descending by velocity score
        unique_results.sort(key=lambda x: x["velocity_score"], reverse=True)
        final_results = unique_results[:limit]

        # Optionally persist in database
        if db is not None:
            self.persist_signals(matched_niche, final_results, db)

        return final_results

    def persist_signals(
        self,
        niche: str,
        signals: List[Dict[str, Any]],
        db: Session,
    ) -> List[TrendingSignal]:
        """Saves trend signals to database with a 48-hour TTL."""
        records = []
        now = utcnow()
        expires = now + timedelta(hours=48)

        for s in signals:
            sig_id = str(uuid.uuid4())
            record = TrendingSignal(
                id=sig_id,
                niche=niche,
                topic=s["topic"],
                source=s.get("source", "trend_sniffer"),
                velocity_score=s.get("velocity_score", 50.0),
                suggested_hook=s.get("suggested_hook", ""),
                suggested_angle=s.get("suggested_angle", ""),
                recommended_format=s.get("recommended_format", "reel"),
                metadata_json=s.get("metadata", {}),
                created_at=now,
                expires_at=expires,
            )
            db.add(record)
            records.append(record)

        try:
            db.commit()
        except Exception:
            db.rollback()

        return records

    def fetch(self, **kwargs: Any) -> List[Dict[str, Any]]:
        """BaseAdapter implementation."""
        niche = kwargs.get("niche", "Tech & AI")
        limit = kwargs.get("limit", 5)
        use_network = kwargs.get("use_network", True)
        return self.sniff(niche=niche, limit=limit, use_network=use_network)
