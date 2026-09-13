"""
base_adapter.py

Abstract base class for all dataset adapters (CSV, Instagram Graph API,
third-party exports, etc). Every adapter's job is simply to produce a
list of raw dict records — schema mapping and validation happen
downstream in schema_mapper.py / data_readiness_agent.py.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseAdapter(ABC):
    """All adapters implement fetch() -> List[raw record dicts]."""

    source_name: str = "unknown"

    @abstractmethod
    def fetch(self, **kwargs: Any) -> List[Dict[str, Any]]:
        """Returns a list of raw, un-mapped records from the source."""
        raise NotImplementedError

    def load(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Convenience wrapper producing the payload shape expected by
        the /data-readiness endpoint and data_readiness_agent.run().
        """
        records = self.fetch(**kwargs)
        return {
            "source": self.source_name,
            "raw_data": records,
        }
