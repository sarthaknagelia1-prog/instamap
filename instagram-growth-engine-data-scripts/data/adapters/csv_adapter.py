"""
csv_adapter.py

Reads a creator-exported CSV (from Instagram's own export tool, or any
third-party analytics export) into a list of raw record dicts.
Column names are left untouched here — schema_mapper.py resolves aliases.
"""

from __future__ import annotations
import csv
from pathlib import Path
from typing import Any, Dict, List

from data.adapters.base_adapter import BaseAdapter


class CSVAdapter(BaseAdapter):
    source_name = "csv_upload"

    def fetch(self, file_path: str, **kwargs: Any) -> List[Dict[str, Any]]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        records: List[Dict[str, Any]] = []
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Drop fully-empty rows, strip whitespace on values
                cleaned = {k: (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
                if any(v not in (None, "") for v in cleaned.values()):
                    records.append(cleaned)

        return records


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 2:
        print("Usage: python csv_adapter.py <path_to_csv>")
        sys.exit(1)

    adapter = CSVAdapter()
    payload = adapter.load(file_path=sys.argv[1])
    print(json.dumps(payload, indent=2)[:2000])
