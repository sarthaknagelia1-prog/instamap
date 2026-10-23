"""
backend/approvals/__init__.py

Approval & Review Layer:
Human-in-the-loop review gating, action classification, and event bus pub/sub.
"""

from backend.approvals.classifier import classify_action
from backend.approvals.events import event_bus, EventBus

__all__ = [
    "classify_action",
    "event_bus",
    "EventBus",
]
