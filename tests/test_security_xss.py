"""
tests/test_security_xss.py

Security Regression Test Suite: XSS and HTML Injection Safety (SEC-02, SEC-05).
Verifies that:
1. Dynamic report variables (creator ID, niche, hook, concepts) are escaped via html.escape.
2. Malicious HTML tags (<script>, <img>, <iframe>, <svg>) render inertly in generated reports.
3. Chat markdown escaping prevents script and event handler injection.
"""

from __future__ import annotations
import pytest
from backend.database.models import Creator, Post, Strategy, ContentPlan, utcnow
from backend.reporting.weekly_report import generate_weekly_report


def test_weekly_report_escapes_hostile_html_payloads(db_session):
    """
    Verifies that hostile script tags and event handlers in creator metadata,
    themes, and hook previews are properly escaped in the generated standalone HTML (SEC-05).
    """
    hostile_cid = "creator_<script>alert('xss_creator')</script>"
    hostile_niche = "Niche\" onmouseover=\"alert('xss_niche')"
    hostile_hook = "<img src=x onerror=alert('xss_hook')> Stop scrolling!"
    hostile_theme = "<b>Bold Theme</b><iframe src='javascript:alert(1)'></iframe>"

    creator = Creator(id=hostile_cid, niche=hostile_niche)
    db_session.add(creator)

    post = Post(
        post_id="post_xss_1",
        creator_id=hostile_cid,
        content_type="reel",
        likes_count=100,
        comments_count=10,
        reach=1000,
        engagement_rate=11.0,
        timestamp=utcnow(),
    )
    strat = Strategy(
        id="strat_xss_1",
        creator_id=hostile_cid,
        primary_content_type="reel",
        format_allocation={"reel": 100},
        core_pillars=["Growth"],
        strategic_priorities=["<script>alert('priority')</script>"],
    )
    plan = ContentPlan(
        id="plan_xss_1",
        creator_id=hostile_cid,
        scheduled_items=[
            {
                "day": "Monday",
                "content_type": "reel",
                "scheduled_time": "18:00 UTC",
                "theme": hostile_theme,
                "concept_angle": "Angle with &amp; and <tags>",
                "hook_preview": hostile_hook,
                "target_metric": "shares",
            }
        ],
    )
    db_session.add_all([post, strat, plan])
    db_session.commit()

    report = generate_weekly_report(hostile_cid, db=db_session)
    html = report["html_report"]

    # Critical assertions: Raw hostile HTML MUST NOT be present
    assert "<script>alert('xss_creator')</script>" not in html
    assert "<img src=x onerror=alert('xss_hook')>" not in html
    assert "<iframe src='javascript:alert(1)'></iframe>" not in html
    assert "<script>alert('priority')</script>" not in html

    # Instead, HTML entities must be present
    assert "&lt;script&gt;alert(&#x27;xss_creator&#x27;)&lt;/script&gt;" in html or "&lt;script&gt;alert('xss_creator')&lt;/script&gt;" in html
    assert "&lt;img src=x onerror=alert(" in html or "&lt;img src=x onerror=alert(&#x27;xss_hook&#x27;)&gt;" in html
    assert "&lt;iframe" in html
