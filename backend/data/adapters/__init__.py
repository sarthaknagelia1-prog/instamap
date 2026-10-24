"""
backend/data/adapters/__init__.py

Data source adapters: CSV, JSON, Paste/Spreadsheet, Meta Account Adapter, and Trend Sniffing.
"""

from backend.data.adapters.base_adapter import BaseAdapter
from backend.data.adapters.csv_adapter import CSVAdapter
from backend.data.adapters.json_adapter import JSONAdapter
from backend.data.adapters.paste_adapter import PasteAdapter
from backend.data.adapters.meta_adapter import MetaAdapter
from backend.data.adapters.trend_sniffing_adapter import TrendSniffingAdapter

__all__ = [
    "BaseAdapter",
    "CSVAdapter",
    "JSONAdapter",
    "PasteAdapter",
    "MetaAdapter",
    "TrendSniffingAdapter",
]
