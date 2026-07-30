"""
shared/utils/helpers.py

General-purpose helper functions shared across agents.
"""

import re
import unicodedata
from datetime import datetime, timezone
from typing import Optional


def normalize_text(text: Optional[str]) -> str:
    """Lowercase, strip accents/punctuation-heavy whitespace, collapse spaces."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("utf-8")
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def safe_int(value, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (ValueError, TypeError):
        return default


def parse_year(date_str: Optional[str]) -> Optional[int]:
    """Best-effort extraction of a 4-digit year from a variety of date formats."""
    if not date_str:
        return None
    match = re.search(r"(19|20)\d{2}", str(date_str))
    return int(match.group(0)) if match else None


def years_since(year: Optional[int]) -> Optional[int]:
    if year is None:
        return None
    current_year = datetime.now(timezone.utc).year
    return max(0, current_year - year)


def truncate(text: Optional[str], max_len: int = 500) -> str:
    if not text:
        return ""
    text = text.strip()
    return text if len(text) <= max_len else text[: max_len - 1].rstrip() + "…"


def chunked(iterable, size: int):
    """Yield successive `size`-sized chunks from a list."""
    for i in range(0, len(iterable), size):
        yield iterable[i : i + size]
