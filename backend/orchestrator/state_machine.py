"""
backend/orchestrator/state_machine.py

LangGraph state machine for the Instagram Growth Engine Orchestrator.
Routes dynamically:
  ingest_context -> analyze -> decide -> (plan | report_only | request_more_data) -> finalize
"""

from __future__ import annotations
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from langgraph.graph import StateGraph, START, END
from sqlalchemy.orm import Session

from backend.agents.schemas import (
    AgentMessage,
    DecisionThresholds,
    OrchestratorAction,
    OrchestratorDecision,
    OrchestratorState,
    utcnow,
)
from backend.database.models import Post, Creator
from backend.analytics.metrics import calculate_aggregate_metrics, calculate_post_engagement_rate
from backend.analytics.trends import detect_trends, find_best_posting_window
from backend.analytics.anomalies import detect_anomalies
from backend.agents.analyst_agent import run_analyst_agent
from backend.agents.strategy_agent import run_strategy_agent
from backend.agents.content_planning_agent import run_content_planning_agent
from backend.agents.content_generation_agent import run_content_generation_agent
from backend.orchestrator.decision_engine import evaluate_decision





def _build_post_dicts(posts: List[Post]) -> List[Dict[str, Any]]:
    post_dicts = []
    for p in posts:
        post_dicts.append({
            "post_id": p.post_id,
            "content_type": p.content_type,
            "timestamp": p.timestamp.isoformat() if p.timestamp else None,
            "likes_count": p.likes_count,
            "comments_count": p.comments_count,
            "shares_count": p.shares_count,
            "saves_count": p.saves_count,
            "reach": p.reach,
            "impressions": p.impressions,
            "engagement_rate": p.engagement_rate or calculate_post_engagement_rate({
                "likes_count": p.likes_count,
                "comments_count": p.comments_count,
                "shares_count": p.shares_count,
                "saves_count": p.saves_count,
                "reach": p.reach,
                "impressions": p.impressions,
            }),
            "caption_text": p.caption_text,
        })
    return post_dicts


# ---------------------------------------------------------
# Node Functions
# ---------------------------------------------------------

def node_fetch_context(state: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """Fetches creator post history from PostgreSQL."""
    t0 = time.time()
    creator_id = state["creator_id"]

    posts = (
        db.query(Post)
        .filter_by(creator_id=creator_id)
        .order_by(Post.timestamp.desc())
        .limit(100)
        .all()
    )

    post_dicts = _build_post_dicts(posts)
    total_posts = len(post_dicts)

    days_since_last = None
    if posts and posts[0].timestamp:
        last_dt = posts[0].timestamp
        if last_dt.tzinfo is None:
            last_dt = last_dt.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - last_dt
        days_since_last = max(0, delta.days)

    trace_msg = {
        "agent_name": "context_fetcher",
        "action_taken": f"Retrieved {total_posts} posts from database",
        "timestamp": utcnow().isoformat(),
        "details": {
            "total_posts": total_posts,
            "days_since_last_post": days_since_last,
        },
        "duration_ms": round((time.time() - t0) * 1000, 2),
    }

    trace = list(state.get("execution_trace", [])) + [trace_msg]

    return {
        "posts": post_dicts,
        "total_posts": total_posts,
        "days_since_last_post": days_since_last,
        "current_node": "fetch_context",
        "execution_trace": trace,
    }


def node_analyze(state: Dict[str, Any]) -> Dict[str, Any]:
    """Runs performance intelligence layer: metrics, trends, anomalies, analyst agent."""
    t0 = time.time()
    posts = state.get("posts", [])
    creator_id = state["creator_id"]

    if not posts:
        return {
            "metrics": {},
            "trends": {},
            "anomalies": [],
            "current_node": "analyze",
            "execution_trace": state.get("execution_trace", []),
        }

    metrics = calculate_aggregate_metrics(posts)
    trends = detect_trends(posts)
    best_window = find_best_posting_window(posts)
    anomalies = detect_anomalies(posts)

    analyst_res = run_analyst_agent(
        creator_id=creator_id,
        metrics=metrics,
        trends=trends,
        best_posting_window=best_window,
        anomalies=anomalies,
        use_llm=False,
    )

    trace_msg = {
        "agent_name": "performance_analyst",
        "action_taken": f"Analyzed {len(posts)} posts: trend is {trends.get('recent_trend')}, avg ER is {metrics.get('average_engagement_rate', 0):.2f}%",
        "timestamp": utcnow().isoformat(),
        "details": {
            "top_content_type": metrics.get("top_content_type"),
            "recent_trend": trends.get("recent_trend"),
            "anomalies_detected": len(anomalies),
        },
        "duration_ms": round((time.time() - t0) * 1000, 2),
    }

    trace = list(state.get("execution_trace", [])) + [trace_msg]

    return {
        "metrics": metrics,
        "trends": trends,
        "anomalies": anomalies,
        "analyst_summary": analyst_res.get("analysis_summary"),
        "recommended_action": analyst_res.get("recommended_action"),
        "current_node": "analyze",
        "execution_trace": trace,
    }


def node_decide(state: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluates rules against thresholds to determine downstream agent routing."""
    t0 = time.time()
    thresholds_dict = state.get("thresholds", {})
    thresholds = DecisionThresholds(**thresholds_dict) if thresholds_dict else DecisionThresholds()

    decision = evaluate_decision(
        total_posts=state.get("total_posts", 0),
        days_since_last_post=state.get("days_since_last_post"),
        metrics=state.get("metrics", {}),
        trends=state.get("trends", {}),
        anomalies=state.get("anomalies", []),
        thresholds=thresholds,
    )

    trace_msg = {
        "agent_name": "decision_engine",
        "action_taken": f"Decision: {decision.action.value}. Reason: {decision.primary_reason}",
        "timestamp": utcnow().isoformat(),
        "details": {
            "action": decision.action.value,
            "reasons": decision.reasons,
            "confidence_score": decision.confidence_score,
        },
        "duration_ms": round((time.time() - t0) * 1000, 2),
    }

    trace = list(state.get("execution_trace", [])) + [trace_msg]

    return {
        "decision": decision.model_dump(),
        "current_node": "decide",
        "execution_trace": trace,
    }


def node_request_more_data(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generates explicit request for fresh or more creator data."""
    t0 = time.time()
    decision = state.get("decision", {})
    reasons = decision.get("reasons", ["Insufficient data"])

    report = {
        "status": "more_data_needed",
        "message": "Orchestrator requires additional post data before generating a growth plan.",
        "reasons": reasons,
        "instructions": [
            "Upload recent CSV export or paste spreadsheet data at POST /data/ingest",
            "Ensure at least 3 recent posts within the past 14 days are included",
        ],
    }

    trace_msg = {
        "agent_name": "data_requester",
        "action_taken": "Generated data ingestion request guidance",
        "timestamp": utcnow().isoformat(),
        "details": {"required_action": "ingest_recent_posts"},
        "duration_ms": round((time.time() - t0) * 1000, 2),
    }

    trace = list(state.get("execution_trace", [])) + [trace_msg]

    return {
        "report_output": report,
        "current_node": "request_more_data",
        "execution_trace": trace,
    }


def node_report_only(state: Dict[str, Any]) -> Dict[str, Any]:
    """Compiles an executive performance report when momentum is strong without needing a strategy pivot."""
    t0 = time.time()
    metrics = state.get("metrics", {})
    trends = state.get("trends", {})
    anomalies = state.get("anomalies", [])

    report = {
        "status": "healthy_momentum",
        "executive_summary": state.get("analyst_summary"),
        "key_metrics": {
            "average_engagement_rate": metrics.get("average_engagement_rate"),
            "top_content_type": metrics.get("top_content_type"),
            "trend": trends.get("recent_trend"),
            "week_over_week_delta": trends.get("week_over_week_delta_pct"),
        },
        "guidance": state.get("recommended_action"),
        "recent_anomalies_flagged": len(anomalies),
    }

    trace_msg = {
        "agent_name": "report_generator",
        "action_taken": "Compiled executive performance report (report_only path)",
        "timestamp": utcnow().isoformat(),
        "details": {"report_status": "healthy_momentum"},
        "duration_ms": round((time.time() - t0) * 1000, 2),
    }

    trace = list(state.get("execution_trace", [])) + [trace_msg]

    return {
        "report_output": report,
        "current_node": "report_only",
        "execution_trace": trace,
    }


def node_plan(state: Dict[str, Any], db: Optional[Session] = None) -> Dict[str, Any]:
    """
    Phase 4 Strategy & Content Generation:
    Executes StrategyAgent -> ContentPlanningAgent -> ContentGenerationAgent.
    """
    creator_id = state["creator_id"]
    metrics = state.get("metrics", {})
    trends = state.get("trends", {})
    posts = state.get("posts", [])
    best_window = find_best_posting_window(posts)

    # 1. Strategy Agent
    t_strat = time.time()
    strategy = run_strategy_agent(
        creator_id=creator_id,
        metrics=metrics,
        trends=trends,
        db=db,
    )
    msg_strat = {
        "agent_name": "strategy_agent",
        "action_taken": f"Formulated strategy: {strategy.get('primary_content_type')} focus, {strategy.get('target_cadence')}",
        "timestamp": utcnow().isoformat(),
        "details": {"format_allocation": strategy.get("format_allocation")},
        "duration_ms": round((time.time() - t_strat) * 1000, 2),
    }

    # 2. Content Planning Agent
    t_plan = time.time()
    plan = run_content_planning_agent(
        creator_id=creator_id,
        strategy=strategy,
        best_posting_window=best_window,
        db=db,
    )
    msg_plan = {
        "agent_name": "content_planning_agent",
        "action_taken": f"Scheduled 7-day calendar with {plan.get('planned_post_count')} posts",
        "timestamp": utcnow().isoformat(),
        "details": {"planned_post_count": plan.get("planned_post_count")},
        "duration_ms": round((time.time() - t_plan) * 1000, 2),
    }

    # 3. Content Generation Agent (drafts top priority item)
    t_draft = time.time()
    sample_item = plan["scheduled_items"][0] if plan.get("scheduled_items") else {"content_type": strategy.get("primary_content_type", "reel"), "theme": "Growth Strategy"}
    draft = run_content_generation_agent(
        creator_id=creator_id,
        plan_item=sample_item,
        plan_id=plan.get("plan_id"),
        db=db,
    )
    msg_draft = {
        "agent_name": "content_generation_agent",
        "action_taken": f"Drafted ready-to-post {draft.get('content_type')} package: '{draft.get('title')}'",
        "timestamp": utcnow().isoformat(),
        "details": {"draft_id": draft.get("draft_id"), "content_type": draft.get("content_type")},
        "duration_ms": round((time.time() - t_draft) * 1000, 2),
    }

    trace = list(state.get("execution_trace", [])) + [msg_strat, msg_plan, msg_draft]

    bundle = {
        "status": "strategy_and_content_bundle_generated",
        "strategy": strategy,
        "content_plan": plan,
        "primary_draft": draft,
    }

    return {
        "strategy_output": bundle,
        "current_node": "plan",
        "execution_trace": trace,
    }


def route_decision(state: Dict[str, Any]) -> str:
    """Conditional router based on decision output."""
    decision = state.get("decision", {})
    action = decision.get("action")

    if action == OrchestratorAction.REQUEST_MORE_DATA.value:
        return "request_more_data"
    elif action == OrchestratorAction.REPORT_ONLY.value:
        return "report_only"
    else:
        return "plan"


# ---------------------------------------------------------
# State Machine Runner
# ---------------------------------------------------------

def run_orchestrator(
    creator_id: str,
    db: Session,
    trigger_event: str = "manual",
    thresholds: Optional[DecisionThresholds] = None,
) -> Dict[str, Any]:
    """
    Executes the full Orchestrator state machine for a creator.
    """
    initial_state = {
        "creator_id": creator_id,
        "trigger_event": trigger_event,
        "thresholds": (thresholds or DecisionThresholds()).model_dump(),
        "execution_trace": [],
        "current_node": "init",
    }

    # Step 1: Context fetch
    state = {**initial_state, **node_fetch_context(initial_state, db)}

    # Step 2: Analyze
    state = {**state, **node_analyze(state)}

    # Step 3: Decide
    state = {**state, **node_decide(state)}

    # Step 4: Conditional branch
    next_branch = route_decision(state)
    if next_branch == "request_more_data":
        state = {**state, **node_request_more_data(state)}
    elif next_branch == "report_only":
        state = {**state, **node_report_only(state)}
    else:
        state = {**state, **node_plan(state, db=db)}

    state["completed_at"] = utcnow().isoformat()
    return state

