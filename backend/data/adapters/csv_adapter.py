"""
backend/data/adapters/csv_adapter.py

Reads a creator-exported CSV into a list of raw record dicts.
Supports reading from a file path or raw CSV string/stream.
"""

from __future__ import annotations
import csv
import io
from pathlib import Path
from typing import Any, Dict, List, TextIO

from backend.data.adapters.base_adapter import BaseAdapter


class CSVAdapter(BaseAdapter):
    source_name = "csv_upload"

    def fetch(self, file_path: str | Path | None = None, content: str | None = None, **kwargs: Any) -> List[Dict[str, Any]]:
        if content is not None:
            f: TextIO = io.StringIO(content)
            return self._parse_csv_stream(f)

        if file_path is not None:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"CSV file not found: {file_path}")
            with path.open("r", encoding="utf-8-sig", newline="") as f:
                return self._parse_csv_stream(f)

        raise ValueError("Either file_path or content must be provided to CSVAdapter.")

    def _parse_csv_stream(self, f: TextIO) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        reader = csv.DictReader(f)
        for row in reader:
            cleaned = {k: (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
            if any(v not in (None, "") for v in cleaned.values()):
                records.append(cleaned)
        return records
