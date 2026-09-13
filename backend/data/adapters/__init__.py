"""
Adapters for various data sources.
"""

from backend.data.adapters.base_adapter import BaseAdapter
from backend.data.adapters.csv_adapter import CSVAdapter
from backend.data.adapters.instagram_graph_adapter import InstagramGraphAdapter

__all__ = ["BaseAdapter", "CSVAdapter", "InstagramGraphAdapter"]
