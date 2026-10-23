"""
backend/data/adapters/paste_adapter.py

Parses raw pasted text (TSV from Google Sheets/Excel, pipe-separated Markdown tables,
or comma-separated values) into a list of raw record dicts.
"""

from __future__ import annotations
import csv
import io
import re
from typing import Any, Dict, List

from backend.data.adapters.base_adapter import BaseAdapter


class PasteAdapter(BaseAdapter):
    source_name = "bulk_paste"

    def fetch(self, text: str, **kwargs: Any) -> List[Dict[str, Any]]:
        """Parses pasted tabular text into a list of record dicts."""
        if not text or not text.strip():
            return []

        cleaned_text = text.strip()

        # Handle Markdown table format: | Header1 | Header2 |
        if "|" in cleaned_text and "\n" in cleaned_text:
            lines = [l.strip() for l in cleaned_text.splitlines() if l.strip()]
            if lines and lines[0].startswith("|"):
                return self._parse_markdown_table(lines)

        # Sniff delimiter (defaulting to tab for spreadsheet copy-paste)
        first_line = cleaned_text.splitlines()[0]
        if "\t" in first_line:
            delimiter = "\t"
        elif ";" in first_line:
            delimiter = ";"
        elif "," in first_line:
            delimiter = ","
        else:
            # Fall back to regex whitespace splitting if tabs/commas absent
            delimiter = "\t"

        f = io.StringIO(cleaned_text)
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

    def _parse_markdown_table(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Parses Markdown table lines with separator row |---|---|."""
        records: List[Dict[str, Any]] = []
        # Header is line 0
        raw_headers = [h.strip() for h in lines[0].strip("|").split("|")]

        data_lines = lines[1:]
        # Filter out markdown divider lines like |---|---|
        if data_lines and re.match(r"^\|?\s*[-:]+[-| :]*\|?$", data_lines[0]):
            data_lines = data_lines[1:]

        for line in data_lines:
            cols = [c.strip() for c in line.strip("|").split("|")]
            if len(cols) == len(raw_headers):
                row = dict(zip(raw_headers, cols))
                if any(v not in (None, "") for v in row.values()):
                    records.append(row)

        return records
