"""
backend/agents/schemas.py

Pydantic schemas and shared contracts across all agents and the orchestrator state machine.
"""

from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class OrchestratorAction(str, Enum):
    GENERATE_FULL_PLAN = "generate_full_plan"
    GENERATE_STRATEGY_ONLY = "generate_strategy_only"
    REPORT_ONLY = "report_only"
    REQUEST_MORE_DATA = "request_more_data"


class DecisionThresholds(BaseModel):
    """Configurable decision rules for the orchestrator."""
    min_posts_required: int = Field(3, description="Minimum number of posts needed to run strategy planning")
    max_staleness_days: int = Field(14, description="Max days since last post before requesting fresh data")
    engagement_drop_threshold_pct: float = Field(-10.0, description="Week-over-week engagement drop % triggering full strategy pivot")
    severe_drop_threshold_pct: float = Field(-25.0, description="Severe anomaly drop % triggering immediate creative overhaul")
    low_engagement_threshold: float = Field(1.5, description="Absolute engagement rate below which a strategy overhaul is advised")


class AgentMessage(BaseModel):
    """Audit log entry for a specific agent/node execution."""
    agent_name: str
    action_taken: str
    timestamp: datetime = Field(default_factory=utcnow)
    details: Dict[str, Any] = Field(default_factory=dict)
    duration_ms: Optional[float] = None


class OrchestratorDecision(BaseModel):
    """Structured decision output from the rule-based decision engine."""
    action: OrchestratorAction
    primary_reason: str
    reasons: List[str] = Field(default_factory=list)
    suggested_focus: Optional[str] = None
    confidence_score: float = Field(1.0, ge=0.0, le=1.0)


class OrchestratorState(BaseModel):
    """
    State object passed between nodes in the LangGraph state machine.
    """
    creator_id: str
    trigger_event: str = "manual"
    thresholds: DecisionThresholds = Field(default_factory=DecisionThresholds)

    # Context & Data
    posts: List[Dict[str, Any]] = Field(default_factory=list)
    total_posts: int = 0
    days_since_last_post: Optional[int] = None

    # Intelligence & Analysis
    metrics: Dict[str, Any] = Field(default_factory=dict)
    trends: Dict[str, Any] = Field(default_factory=dict)
    anomalies: List[Dict[str, Any]] = Field(default_factory=list)
    analyst_summary: Optional[str] = None
    recommended_action: Optional[str] = None

    # Decision
    decision: Optional[OrchestratorDecision] = None

    # Generated Artifacts
    strategy_output: Optional[Dict[str, Any]] = None
    content_plan: Optional[Dict[str, Any]] = None
    report_output: Optional[Dict[str, Any]] = None

    # Observability
    execution_trace: List[AgentMessage] = Field(default_factory=list)
    current_node: str = "init"
    error: Optional[str] = None
    completed_at: Optional[datetime] = None
