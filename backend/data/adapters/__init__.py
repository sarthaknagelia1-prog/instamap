"""
backend/data/adapters/__init__.py

Data source adapters: CSV, JSON, Paste/Spreadsheet, and optional external adapters.
"""

from backend.data.adapters.base_adapter import BaseAdapter
from backend.data.adapters.csv_adapter import CSVAdapter
from backend.data.adapters.json_adapter import JSONAdapter
from backend.data.adapters.paste_adapter import PasteAdapter

__all__ = [
    "BaseAdapter",
    "CSVAdapter",
    "JSONAdapter",
    "PasteAdapter",
]
