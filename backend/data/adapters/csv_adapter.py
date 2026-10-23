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
            return self._parse_csv_string(content)

        if file_path is not None:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"CSV file not found: {file_path}")
            with path.open("r", encoding="utf-8-sig", newline="") as f:
                return self._parse_csv_string(f.read())

        raise ValueError("Either file_path or content must be provided to CSVAdapter.")

    def _parse_csv_string(self, content_str: str) -> List[Dict[str, Any]]:
        if not content_str.strip():
            return []

        # Sniff delimiter (handles comma, tab, semicolon)
        delimiter = ","
        first_few_lines = "\n".join(content_str.strip().splitlines()[:5])
        try:
            dialect = csv.Sniffer().sniff(first_few_lines, delimiters=",\t;")
            delimiter = dialect.delimiter
        except Exception:
            # Fallback heuristic
            if "\t" in first_few_lines and first_few_lines.count("\t") > first_few_lines.count(","):
                delimiter = "\t"
            elif ";" in first_few_lines and first_few_lines.count(";") > first_few_lines.count(","):
                delimiter = ";"

        f = io.StringIO(content_str)
        reader = csv.DictReader(f, delimiter=delimiter)
        records: List[Dict[str, Any]] = []
        for row in reader:
            cleaned = {
                (k.strip() if isinstance(k, str) else k): (v.strip() if isinstance(v, str) else v)
                for k, v in row.items() if k is not None
            }
            if any(v not in (None, "") for v in cleaned.values()):
                records.append(cleaned)
        return records

