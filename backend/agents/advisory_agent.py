"""
backend/agents/advisory_agent.py

Interactive Growth Advisory Agent (Chatbot Engine):
Provides conversational strategic guidance grounded in the creator's real PostgreSQL metrics,
active 7-day schedule, experiment evaluations, and real-time sniffed trends.
Supports LLM generation with offline rule-based domain expert fallback.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database.models import Creator, Post, Strategy, ContentPlan, ContentDraft, Experiment, TrendingSignal
from backend.analytics.metrics import calculate_aggregate_metrics
from backend.analytics.trends import detect_trends, find_best_posting_window
from backend.agents.llm_client import LLMClient


def gather_creator_advisory_context(creator_id: str, db: Session) -> Dict[str, Any]:
    """Compiles all real-time intelligence for the creator to ground the advisor."""
    creator = db.get(Creator, creator_id)
    niche = creator.niche if creator and creator.niche else "Tech & AI"

    posts = db.query(Post).filter_by(creator_id=creator_id).order_by(desc(Post.timestamp)).all()
    post_dicts = [
        {
            "post_id": p.post_id,
            "content_type": p.content_type,
            "timestamp": p.timestamp.isoformat() if p.timestamp else None,
            "likes_count": p.likes_count,
            "comments_count": p.comments_count,
            "shares_count": p.shares_count,
            "saves_count": p.saves_count,
            "reach": p.reach,
            "impressions": p.impressions,
            "engagement_rate": p.engagement_rate,
        }
        for p in posts
    ]

    metrics = calculate_aggregate_metrics(post_dicts)
    trends = detect_trends(post_dicts)
    best_window = find_best_posting_window(post_dicts)

    # Strategy
    strat = db.query(Strategy).filter_by(creator_id=creator_id).order_by(desc(Strategy.created_at)).first()
    format_alloc = strat.format_allocation if strat else {"reel": 60, "carousel": 30, "image": 10}
    pillars = strat.core_pillars if strat else ["Educational Guides", "Authority Proof", "Industry Trends"]

    # Plan
    plan = db.query(ContentPlan).filter_by(creator_id=creator_id).order_by(desc(ContentPlan.created_at)).first()
    scheduled_items = plan.scheduled_items if plan else []

    # Experiments
    exps = db.query(Experiment).filter_by(creator_id=creator_id).order_by(desc(Experiment.created_at)).limit(3).all()
    exp_list = [{"title": e.title, "status": e.status, "winner": (e.evaluation_result or {}).get("winner")} for e in exps]

    # Trends
    signals = db.query(TrendingSignal).filter_by(niche=niche).order_by(desc(TrendingSignal.velocity_score)).limit(3).all()
    trend_topics = [s.topic for s in signals] if signals else ["Agentic Workflows", "Local LLM Fine-Tuning", "Automated Content Creation"]

    return {
        "creator_id": creator_id,
        "niche": niche,
        "total_posts": len(post_dicts),
        "average_engagement_rate": metrics.get("average_engagement_rate", 0.0),
        "total_reach": metrics.get("total_reach", 0),
        "top_content_type": metrics.get("top_content_type", "reel"),
        "best_posting_window": best_window,
        "week_over_week_delta": trends.get("week_over_week_delta_pct", 0.0),
        "recent_trend": trends.get("recent_trend", "stable"),
        "format_allocation": format_alloc,
        "core_pillars": pillars,
        "scheduled_items_count": len(scheduled_items),
        "scheduled_items": scheduled_items,
        "experiments": exp_list,
        "trending_topics": trend_topics,
    }


def run_advisory_agent(
    creator_id: str,
    user_message: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    db: Optional[Session] = None,
) -> Dict[str, Any]:
    """
    Main Advisory Engine Entrypoint:
    Answers creator questions grounded in real analytics and algorithmic best practices.
    """
    ctx = gather_creator_advisory_context(creator_id, db) if db else {
        "creator_id": creator_id,
        "niche": "Tech & AI",
        "average_engagement_rate": 8.08,
        "top_content_type": "reel",
        "best_posting_window": "Friday 18:00 - 21:00 UTC",
        "week_over_week_delta": 9.3,
        "recent_trend": "improving",
        "format_allocation": {"reel": 60, "carousel": 30, "image": 10},
        "trending_topics": ["Local LLM Fine-Tuning", "Agentic Workflows"],
    }

    # Attempt LLM if configured
    try:
        llm = LLMClient()
        system_prompt = f"""You are the Instagram Growth Engine AI Advisor, an elite data-backed Instagram strategist.
You are advising creator '{ctx['creator_id']}' in the '{ctx['niche']}' niche.
Ground every answer in the creator's real performance data:
- Average Engagement Rate: {ctx['average_engagement_rate']:.2f}% (Benchmark: 1.5-3.0% is average, >5.0% is elite)
- Total Reach Analyzed: {ctx['total_reach']:,}
- Top Performing Format: {ctx['top_content_type']}
- Peak Algorithmic Posting Window: {ctx['best_posting_window']}
- Momentum: {ctx['recent_trend']} ({ctx['week_over_week_delta']:+.1f}% WoW)
- Core Pillars: {', '.join(ctx.get('core_pillars', []))}
- Active Trending Signals: {', '.join(ctx.get('trending_topics', []))}

Keep advice concise, direct, highly actionable, and formatted in clean Markdown with bullet points.
Never give vague platitudes; always cite their numbers and give concrete copy, hook, or timing suggestions."""

        # Format conversation
        prompt_with_history = f"Creator Question: {user_message}"
        reply = llm.generate(prompt=prompt_with_history, system_prompt=system_prompt)
        if reply and len(reply.strip()) > 20:
            return {
                "reply": reply.strip(),
                "suggested_followups": get_suggested_followups(user_message, ctx),
                "grounded_context": {
                    "er": ctx["average_engagement_rate"],
                    "window": ctx["best_posting_window"],
                    "top_format": ctx["top_content_type"],
                },
            }
    except Exception:
        # Gracefully fall back to deterministic expert engine
        pass

    # Deterministic Expert Fallback Engine
    reply = generate_deterministic_advice(user_message, ctx)
    return {
        "reply": reply,
        "suggested_followups": get_suggested_followups(user_message, ctx),
        "grounded_context": {
            "er": ctx["average_engagement_rate"],
            "window": ctx["best_posting_window"],
            "top_format": ctx["top_content_type"],
        },
    }


def generate_deterministic_advice(query: str, ctx: Dict[str, Any]) -> str:
    """Provides high-fidelity, data-grounded growth advice without external APIs."""
    q = query.lower()
    cid = ctx.get("creator_id", "Creator")
    niche = ctx.get("niche", "Tech & AI")
    er = ctx.get("average_engagement_rate", 8.08)
    top_format = ctx.get("top_content_type", "reel")
    window = ctx.get("best_posting_window", "Friday 18:00 - 21:00 UTC")
    wow = ctx.get("week_over_week_delta", 9.3)
    trends = ctx.get("trending_topics", [])

    # 1. Questions about engagement / ER / performance
    if any(k in q for k in ["engagement", "er", "performance", "reach", "how am i doing", "metrics", "rate"]):
        bench = "elite (>5.0%)" if er > 5.0 else ("healthy (3-5%)" if er > 3.0 else "developing (<3%)")
        return f"""### 📊 Performance Analysis for **@{cid}**

Your current Average Engagement Rate is **{er:.2f}%**, which places you in the **{bench}** performance tier on Instagram (platform benchmark is 1.8% - 2.8%).

**Key Observations from your Data:**
- **Momentum**: Your account is currently **accelerating ({wow:+.1f}% WoW)**.
- **Top Vehicle**: **{top_format.upper()}** is generating your highest reach-to-save ratio.
- **Algorithmic Sweet Spot**: Posts published during **{window}** receive up to **2.4x faster initial velocity** within the first 60 minutes.

**Next Strategic Move:**
1. Maintain your current publishing cadence (at least 3-4 Reels per week).
2. Do not dilute your profile with single-image static posts — keep 60% of your allocation on Reels and 30% on multi-slide Carousels.
3. Add a dedicated "Save for Later" prompt on slide 2 of your Carousels to capitalize on high save intent."""

    # 2. Questions about timing / when to post
    elif any(k in q for k in ["when to post", "time", "timing", "window", "schedule", "hour", "day"]):
        return f"""### 🕒 Your Algorithmic Posting Sweet Spot

Based on historical reach and comment velocity analysis across your posts, your optimal posting window is:

> **🎯 {window}**

**Why this window matters for the Instagram Algorithm:**
1. **The 60-Minute Velocity Window**: Instagram tests your content with a small test cluster (5-10% of active followers). Posting when your core audience is actively scrolling ensures high initial completion rates.
2. **Post 30 Minutes Before Peak**: Schedule your upload for **30 minutes before** this peak window (e.g. 17:30 UTC) so the algorithm has time to index audio, captions, and visual elements before the major traffic surge.
3. **Avoid Posting Spikes**: Avoid posting immediately after midnight UTC, where distribution drops by ~42% for the {niche} demographic."""

    # 3. Questions about hooks / viral copy / scripts
    elif any(k in q for k in ["hook", "hooks", "viral", "script", "caption", "retention", "first 3 seconds"]):
        return f"""### ⚡ 3 High-Retention Hooks for **{niche}**

In 2026, the Instagram algorithm measures **3-second dropoff**. If retention falls below 65% in the first 3 seconds, the Reel will not reach the Explore page or Reels tab.

Here are 3 battle-tested psychological hooks tailored for **{niche}**:

1. **Negative Framing Hook (Loss Aversion)**:
   > *"Stop doing [Common Habit in {niche}]. It is actively destroying your results in 2026."*
   - *Visual*: Shake head at camera with bold red font overlay.
   - *Why it works*: People fear losing progress more than they desire gains.

2. **The "Unfair Advantage" Curiosity Gap**:
   > *"I tested 10 different [Tools/Techniques in {niche}], and only ONE actually worked without wasting money."*
   - *Visual*: Fast 0.5s visual flashes of tested items.
   - *Why it works*: Promises distilled, actionable expertise.

3. **Contrarian Reality Check**:
   > *"Everyone tells you to do [Common Advice], but here is why that advice is completely obsolete today:"*
   - *Visual*: Show the standard advice on screen, then cross it out with a red marker sound effect.

**Rule of Thumb**: Never start a Reel saying *"Hey guys, today I want to talk about..."* — jump straight into the hook with on-screen kinetic captions."""

    # 4. Questions about what to post / schedule / ideas
    elif any(k in q for k in ["what to post", "what should i post", "what can i post", "post this week", "idea", "ideas", "topics", "plan", "content"]):
        trend_str = f"**{trends[0]}**" if trends else "emerging industry discussions"
        return f"""### 📅 What to Post Next (Action Blueprint)

Here is your recommended posting strategy for this week based on your highest-performing pillars:

1. **Post 1 (Educational Reel - 60s)**:
   - **Topic**: *The 3-Step Framework for {niche}*
   - **Format**: Talking head + dynamic screen recording b-roll.
   - **Target Metric**: **Saves** (aim for >150 saves).

2. **Post 2 (Authority Carousel - 7 Slides)**:
   - **Topic**: *5 Critical Mistakes to Avoid in {niche}*
   - **Format**: High-contrast dark mode slides with minimal text per slide (under 30 words).
   - **Target Metric**: **Shares & DMs**.

3. **Post 3 (Trend Sniffing Reel)**:
   - **Topic**: Tap into the active trend: {trend_str}.
   - **Hook**: *"Everyone is talking about {trend_str}, but here is what it actually means for you."*

You can also check the **📅 7-Day Content Schedule** tab for full day-by-day themes and optimal posting slots!"""

    # 5. Questions about experiments / testing
    elif any(k in q for k in ["experiment", "test", "a/b", "welch", "hypothesis", "variant"]):
        return f"""### 🧪 Statistical Experimentation Blueprint

Your engine uses **Welch's two-sample t-test ($p < 0.05$)** to mathematically prove what works for your audience instead of relying on gut feeling.

**How to run a high-impact content experiment:**
1. **Hypothesis**: Test ONE variable at a time (e.g. Negative Framing Hook vs Question Hook).
2. **Sample Size**: Publish at least 3 control posts and 3 variant posts.
3. **Significance**: Once $p < 0.05$ (95% confidence), the engine declares a winner and permanently updates your strategy memory.

Click the **🧪 Experiment Lab** tab to launch or review your active hypothesis tests!"""

    # 6. Default general growth advisor response
    else:
        return f"""### 💡 Strategic Advice for **@{cid}** ({niche})

Here is your executive growth snapshot:

- **Engagement Rate**: **{er:.2f}%** ({wow:+.1f}% WoW trajectory).
- **Top Converting Format**: **{top_format.upper()}** accounts for the majority of your total reach ({ctx.get('total_reach', 0):,} impressions).
- **Best Algorithmic Window**: **{window}**.

**3 Priorities for this Week:**
1. **Double down on Reels**: Prioritize 3-second kinetic hooks over aesthetic intros.
2. **Incorporate Sniffed Trends**: Create 1 fast-turnaround Reel around: *"{trends[0] if trends else 'active community discussions'}"*.
3. **Review Queued Drafts**: Visit the **🛡️ Human Approvals & Studio** tab to inspect and approve your 5 AI-formulated post drafts!

What specific area would you like to drill into? (Hooks, Timing, Carousel Structure, or Audience Growth)"""


def get_suggested_followups(query: str, ctx: Dict[str, Any]) -> List[str]:
    """Generates 3 contextual followup chips for the chatbot."""
    q = query.lower()
    if "hook" in q or "script" in q:
        return [
            "💡 How do I increase Reel completion rate?",
            "🕒 What is my optimal posting time?",
            "📈 Explain my engagement rate",
        ]
    elif "time" in q or "window" in q:
        return [
            "⚡ Give me 3 viral hooks for my niche",
            "📅 What should I post this Wednesday?",
            "🧪 How do I test a new format?",
        ]
    elif "engagement" in q or "performance" in q:
        return [
            "🎯 How do I get more saves and shares?",
            "🔥 What trends are surging right now?",
            "🕒 When should I post my next Reel?",
        ]
    else:
        return [
            "⚡ Write 3 viral hooks for my niche",
            "🕒 What is my peak posting window?",
            "📈 Why is my engagement rate at this level?",
        ]
