"""
shared/utils/helpers.py

General-purpose helper functions shared across agents.
"""

from __future__ import annotations

import json
import re
import time
import unicodedata
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

T = TypeVar("T")


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


def extract_json(text: str) -> Any:
    """
    LLMs sometimes wrap JSON in markdown fences or add a preamble.
    This pulls out the first {...} or [...] block and parses it.
    Raises ValueError if nothing parseable is found.
    """
    cleaned = text.strip()
    cleaned = re.sub(r"^```(json)?", "", cleaned.strip())
    cleaned = re.sub(r"```$", "", cleaned.strip())
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    for open_ch, close_ch in (("{", "}"), ("[", "]")):
        start = cleaned.find(open_ch)
        end = cleaned.rfind(close_ch)
        if start != -1 and end != -1 and end > start:
            candidate = cleaned[start : end + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue

    raise ValueError(f"Could not extract JSON from model output: {text[:200]!r}")


def retry(times: int = 3, delay_seconds: float = 1.5, backoff: float = 2.0):
    """Simple retry decorator with exponential backoff for flaky API calls."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exc: Exception | None = None
            wait = delay_seconds
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:  # noqa: BLE001
                    last_exc = exc
                    if attempt == times:
                        break
                    time.sleep(wait)
                    wait *= backoff
            assert last_exc is not None
            raise last_exc

        return wrapper

    return decorator


def chunk_text(text: str, max_chars: int = 4000) -> list[str]:
    """Split long text into chunks on paragraph boundaries where possible."""
    if len(text) <= max_chars:
        return [text]

    chunks: list[str] = []
    current = ""
    for para in text.split("\n\n"):
        if len(current) + len(para) + 2 <= max_chars:
            current = f"{current}\n\n{para}" if current else para
        else:
            if current:
                chunks.append(current)
            current = para
    if current:
        chunks.append(current)
    return chunks
