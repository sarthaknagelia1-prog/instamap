"""
backend/data/adapters/json_adapter.py

Parses JSON datasets into a list of raw record dicts.
Supports JSON file paths, raw JSON strings, and common wrappers
(e.g., {"posts": [...]}, {"data": [...]}, {"items": [...]}).
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List

from backend.data.adapters.base_adapter import BaseAdapter


class JSONAdapter(BaseAdapter):
    source_name = "json_input"

    def fetch(
        self,
        file_path: str | Path | None = None,
        content: str | None = None,
        data: List[Dict[str, Any]] | Dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Parses records from direct Python data, raw JSON content string, or file path."""
        if data is not None:
            return self._unwrap_data(data)

        if content is not None:
            parsed = json.loads(content)
            return self._unwrap_data(parsed)

        if file_path is not None:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"JSON file not found: {file_path}")
            with path.open("r", encoding="utf-8") as f:
                parsed = json.load(f)
                return self._unwrap_data(parsed)

        raise ValueError("Either data, content, or file_path must be provided to JSONAdapter.")

    def _unwrap_data(self, raw: Any) -> List[Dict[str, Any]]:
        """Unwraps list of records from potential root wrappers."""
        if isinstance(raw, list):
            return [item for item in raw if isinstance(item, dict)]

        if isinstance(raw, dict):
            # Check common collection keys
            for key in ("posts", "data", "items", "records", "results", "media"):
                if key in raw and isinstance(raw[key], list):
                    return [item for item in raw[key] if isinstance(item, dict)]
            # If it's a single post record
            return [raw]

        return []
