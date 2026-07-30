"""
shared/utils/validators.py

Lightweight validation helpers (kept dependency-free / not tied to pydantic
so any of the four modules can use them regardless of their web framework).
"""

from typing import Any, Dict


class ValidationError(Exception):
    """Raised when input data fails a validation check."""


def require_non_empty_str(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"'{field_name}' must be a non-empty string")
    return value.strip()


def require_positive_int(value: Any, field_name: str, max_value: int = 1000) -> int:
    try:
        ivalue = int(value)
    except (ValueError, TypeError):
        raise ValidationError(f"'{field_name}' must be an integer")
    if ivalue <= 0 or ivalue > max_value:
        raise ValidationError(f"'{field_name}' must be between 1 and {max_value}")
    return ivalue


def validate_search_request(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Validate the incoming payload for a literature search request."""
    query = require_non_empty_str(payload.get("query", ""), "query")
    top_k = payload.get("top_k", 20)
    top_k = require_positive_int(top_k, "top_k", max_value=100)

    sources = payload.get("sources")
    if sources is not None and not isinstance(sources, list):
        raise ValidationError("'sources' must be a list of strings if provided")

    return {"query": query, "top_k": top_k, "sources": sources}
