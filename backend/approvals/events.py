"""
backend/approvals/events.py

Lightweight In-Process Event Bus:
Facilitates asynchronous, decoupled messaging across system boundaries:
- data.uploaded
- performance.drop_detected
- experiment.completed
- approval.created
- approval.resolved
"""

from __future__ import annotations
import inspect
from typing import Any, Callable, Dict, List


class EventBus:
    """In-memory pub/sub event dispatcher."""

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, topic: str, handler: Callable) -> None:
        """Registers a callback handler for a given topic."""
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        if handler not in self._subscribers[topic]:
            self._subscribers[topic].append(handler)

    def publish(self, topic: str, data: Dict[str, Any]) -> List[Any]:
        """Dispatches an event to all registered topic handlers."""
        handlers = self._subscribers.get(topic, [])
        wildcard_handlers = self._subscribers.get("*", [])
        all_handlers = handlers + [h for h in wildcard_handlers if h not in handlers]

        results = []
        for handler in all_handlers:
            try:
                res = handler(data)
                results.append(res)
            except Exception as e:
                results.append({"error": str(e), "handler": handler.__name__})
        return results

    def clear(self) -> None:
        """Clears all event subscriptions (useful in test teardowns)."""
        self._subscribers.clear()


# Global singleton instance
event_bus = EventBus()
