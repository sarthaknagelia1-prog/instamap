"""
backend/reporting/weekly_report.py

Weekly Executive Growth Report Generator:
Compiles creator performance metrics, trajectory momentum, active format allocations,
experiment evaluation outcomes, and the "What to Post This Week" briefing into
structured JSON, GitHub-flavored Markdown, and printable standalone HTML.
"""

from __future__ import annotations
import html
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database.models import Creator, Post, Strategy, ContentPlan, ContentDraft, Experiment, TrendingSignal, utcnow
from backend.analytics.metrics import calculate_aggregate_metrics
from backend.analytics.trends import detect_trends, find_best_posting_window


def generate_weekly_report(creator_id: str, db: Session) -> Dict[str, Any]:
    """Generates comprehensive weekly growth report for a creator."""
    creator = db.get(Creator, creator_id)
    niche = creator.niche if creator and creator.niche else "Creator"

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

    # Latest Strategy
    strategy_rec = db.query(Strategy).filter_by(creator_id=creator_id).order_by(desc(Strategy.created_at)).first()
    format_alloc = strategy_rec.format_allocation if strategy_rec else {"reel": 60, "carousel": 30, "image": 10}
    pillars = strategy_rec.core_pillars if strategy_rec else ["Educational Guide", "Authority Proof", "Behind the Scenes", "Trends"]
    priorities = strategy_rec.strategic_priorities if strategy_rec else ["Maintain publishing cadence", "Focus on high-retention hooks"]

    # Latest Content Plan
    plan_rec = db.query(ContentPlan).filter_by(creator_id=creator_id).order_by(desc(ContentPlan.created_at)).first()
    scheduled_items = plan_rec.scheduled_items if plan_rec else []

    # Experiments
    exps = db.query(Experiment).filter_by(creator_id=creator_id).order_by(desc(Experiment.created_at)).limit(3).all()
    exp_summaries = []
    for e in exps:
        exp_summaries.append({
            "title": e.title,
            "status": e.status,
            "winner": (e.evaluation_result or {}).get("winner"),
            "confidence_pct": (e.evaluation_result or {}).get("confidence_pct", 0.0),
        })

    # Render Markdown
    md_lines = [
        f"# Weekly Executive Growth Briefing: {creator_id}",
        f"**Generated**: {utcnow().strftime('%Y-%m-%d %H:%M UTC')} | **Niche**: {niche}\n",
        "---",
        "## 1. Executive Performance Summary",
        f"- **Average Engagement Rate**: {metrics.get('average_engagement_rate', 0.0):.2f}%",
        f"- **Performance Trajectory**: `{trends.get('recent_trend', 'stable').upper()}` (Week-over-Week: {trends.get('week_over_week_delta_pct', 0.0):+.1f}%)",
        f"- **Total Reach Analyzed**: {metrics.get('total_reach', 0):,}",
        f"- **Optimal Algorithmic Window**: `{best_window}`",
        f"- **Top Converting Format**: `{metrics.get('top_content_type', 'reel').upper()}`\n",
        "## 2. Active Strategy & Format Allocation",
        f"- **Format Distribution**: " + " / ".join([f"{k.capitalize()}: {v}%" for k, v in format_alloc.items()]),
        "- **Strategic Pillars**: " + ", ".join(pillars),
        "- **Top Priorities**:",
    ]
    for p in priorities[:3]:
        md_lines.append(f"  - {p}")

    md_lines.extend([
        "\n## 3. What to Post This Week (Actionable Briefing)",
    ])
    if scheduled_items:
        for item in scheduled_items:
            md_lines.append(f"### {item.get('day')} — {item.get('content_type', 'reel').upper()} ({item.get('scheduled_time')})")
            md_lines.append(f"- **Theme**: {item.get('theme')}")
            md_lines.append(f"- **Concept Angle**: {item.get('concept_angle')}")
            if item.get("hook_preview"):
                md_lines.append(f"- **Suggested Hook**: *\"{item.get('hook_preview')}\"*")
            md_lines.append(f"- **Target Metric**: `{item.get('target_metric')}`\n")
    else:
        md_lines.append("_No active content plan scheduled. Trigger orchestrator or generate plan._\n")

    if exp_summaries:
        md_lines.extend(["## 4. Experiment Lab Status"])
        for es in exp_summaries:
            status_badge = "Conclusive Winner" if "conclusive" in es['status'] else es['status'].capitalize()
            md_lines.append(f"- **{es['title']}**: `{status_badge}` ({es['confidence_pct']:.1f}% confidence)")

    rendered_markdown = "\n".join(md_lines)

    # Render Standalone Styled HTML with Strict XSS Escaping (SEC-05)
    esc_creator_id = html.escape(str(creator_id))
    esc_niche = html.escape(str(niche))
    esc_best_window = html.escape(str(best_window))

    priorities_html = "".join([f"<li>{html.escape(str(p))}</li>" for p in priorities[:3]])
    format_alloc_html = " / ".join([f"{html.escape(str(k)).capitalize()}: {v}%" for k, v in format_alloc.items()])

    scheduled_html_items = []
    for item in scheduled_items:
        day_str = html.escape(str(item.get("day", "")))
        ctype_str = html.escape(str(item.get("content_type", "reel")))
        time_str = html.escape(str(item.get("scheduled_time", "")))
        target_str = html.escape(str(item.get("target_metric", "")))
        theme_str = html.escape(str(item.get("theme", "")))
        angle_str = html.escape(str(item.get("concept_angle", "")))
        hook_str = html.escape(str(item.get("hook_preview", ""))) if item.get("hook_preview") else ""

        item_card = f"""
        <div class="schedule-item">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <strong style="font-size:16px; color:#38bdf8;">{day_str}</strong>
                <span class="badge">{ctype_str}</span>
            </div>
            <div style="font-size:13px; color:#94a3b8; margin: 4px 0;">Time: {time_str} | Target: {target_str}</div>
            <div style="margin-top:6px;"><strong>Theme:</strong> {theme_str} - {angle_str}</div>
            {f'<div class="hook-quote">"{hook_str}"</div>' if hook_str else ''}
        </div>"""
        scheduled_html_items.append(item_card)

    items_block = "".join(scheduled_html_items) if scheduled_html_items else "<p>No content plan currently scheduled.</p>"

    rendered_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Weekly Growth Briefing - {esc_creator_id}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #0f172a; color: #f8fafc; padding: 40px; margin: 0; line-height: 1.6; }}
        .container {{ max-width: 860px; margin: 0 auto; background: #1e293b; border-radius: 12px; padding: 36px; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3); border: 1px solid #334155; }}
        h1 {{ color: #38bdf8; font-size: 26px; margin-top: 0; border-bottom: 2px solid #334155; padding-bottom: 12px; }}
        h2 {{ color: #e2e8f0; font-size: 19px; margin-top: 28px; border-bottom: 1px solid #334155; padding-bottom: 8px; }}
        .badge {{ background: #0ea5e9; color: white; padding: 3px 8px; border-radius: 6px; font-size: 12px; font-weight: 600; text-transform: uppercase; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin: 20px 0; }}
        .card {{ background: #0f172a; padding: 18px; border-radius: 8px; border: 1px solid #334155; }}
        .metric-label {{ color: #94a3b8; font-size: 13px; text-transform: uppercase; }}
        .metric-val {{ font-size: 24px; font-weight: 700; color: #f8fafc; margin-top: 4px; }}
        .schedule-item {{ background: #0f172a; border-left: 4px solid #38bdf8; padding: 14px 18px; margin-bottom: 12px; border-radius: 0 8px 8px 0; }}
        .hook-quote {{ background: #1e293b; padding: 8px 12px; border-radius: 6px; font-style: italic; color: #cbd5e1; margin-top: 6px; border: 1px dashed #475569; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Weekly Executive Growth Briefing</h1>
        <p><strong>Creator:</strong> {esc_creator_id} &nbsp;|&nbsp; <strong>Niche:</strong> {esc_niche} &nbsp;|&nbsp; <strong>Generated:</strong> {utcnow().strftime('%B %d, %Y')}</p>
        
        <h2>1. Key Metrics & Momentum</h2>
        <div class="grid">
            <div class="card">
                <div class="metric-label">Avg Engagement</div>
                <div class="metric-val">{metrics.get('average_engagement_rate', 0.0):.2f}%</div>
            </div>
            <div class="card">
                <div class="metric-label">Trajectory (WoW)</div>
                <div class="metric-val">{trends.get('week_over_week_delta_pct', 0.0):+.1f}%</div>
            </div>
            <div class="card">
                <div class="metric-label">Total Reach</div>
                <div class="metric-val">{metrics.get('total_reach', 0):,}</div>
            </div>
            <div class="card">
                <div class="metric-label">Optimal Window</div>
                <div class="metric-val" style="font-size: 15px; margin-top: 8px;">{esc_best_window}</div>
            </div>
        </div>

        <h2>2. Format Allocation & Priorities</h2>
        <p><strong>Format Allocation:</strong> {format_alloc_html}</p>
        <p><strong>Strategic Priorities:</strong></p>
        <ul>
            {priorities_html}
        </ul>

        <h2>3. What to Post This Week</h2>
        {items_block}
    </div>
</body>
</html>"""

    return {
        "creator_id": creator_id,
        "niche": niche,
        "generated_at": utcnow().isoformat(),
        "metrics": metrics,
        "trends": trends,
        "best_posting_window": best_window,
        "strategy": {
            "format_allocation": format_alloc,
            "core_pillars": pillars,
            "strategic_priorities": priorities,
        },
        "content_schedule": scheduled_items,
        "experiments": exp_summaries,
        "markdown_report": rendered_markdown,
        "html_report": rendered_html,
    }
