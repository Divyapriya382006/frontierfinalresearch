"""
shared/utils/config.py

Centralized configuration for all agents in ResearchAgentX.
Loads settings from environment variables (with sane defaults) so every
person's module (1-4) can import a single source of truth.
"""

import os
from dataclasses import dataclass, field
from typing import Optional

from dotenv import find_dotenv, load_dotenv


load_dotenv(find_dotenv(usecwd=True), override=False)


def _get_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


def _get_int(name: str, default: int) -> int:
    val = os.getenv(name)
    try:
        return int(val) if val is not None else default
    except ValueError:
        return default


def _get_float(name: str, default: float) -> float:
    val = os.getenv(name)
    try:
        return float(val) if val is not None else default
    except ValueError:
        return default


@dataclass
class Settings:
    # --- General ---
    env: str = field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    # --- Person 1: Literature search & ranking ---
    semantic_scholar_api_key: Optional[str] = field(
        default_factory=lambda: os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    )
    semantic_scholar_base_url: str = field(
        default_factory=lambda: os.getenv(
            "SEMANTIC_SCHOLAR_BASE_URL", "https://api.semanticscholar.org/graph/v1"
        )
    )
    arxiv_base_url: str = field(
        default_factory=lambda: os.getenv("ARXIV_BASE_URL", "http://export.arxiv.org/api/query")
    )
    openalex_base_url: str = field(
        default_factory=lambda: os.getenv("OPENALEX_BASE_URL", "https://api.openalex.org")
    )
    openalex_mailto: Optional[str] = field(
        default_factory=lambda: os.getenv("OPENALEX_MAILTO")
    )
    google_scholar_base_url: str = field(
        default_factory=lambda: os.getenv("GOOGLE_SCHOLAR_BASE_URL", "https://scholar.google.com/scholar")
    )
    tavily_base_url: str = field(
        default_factory=lambda: os.getenv("TAVILY_BASE_URL", "https://api.tavily.com/search")
    )
    tavily_api_key: Optional[str] = field(default_factory=lambda: os.getenv("TAVILY_API_KEY"))

    request_timeout_seconds: int = field(default_factory=lambda: _get_int("REQUEST_TIMEOUT_SECONDS", 15))
    max_results_per_source: int = field(default_factory=lambda: _get_int("MAX_RESULTS_PER_SOURCE", 30))
    max_retries: int = field(default_factory=lambda: _get_int("MAX_RETRIES", 3))
    retry_backoff_seconds: float = field(default_factory=lambda: _get_float("RETRY_BACKOFF_SECONDS", 1.5))

    # Ranking weights (must roughly sum to 1.0, but not enforced strictly)
    weight_relevance: float = field(default_factory=lambda: _get_float("WEIGHT_RELEVANCE", 0.6))
    weight_citations: float = field(default_factory=lambda: _get_float("WEIGHT_CITATIONS", 0.2))
    weight_recency: float = field(default_factory=lambda: _get_float("WEIGHT_RECENCY", 0.1))
    weight_venue_quality: float = field(default_factory=lambda: _get_float("WEIGHT_VENUE_QUALITY", 0.1))

    duplicate_similarity_threshold: float = field(
        default_factory=lambda: _get_float("DUPLICATE_SIMILARITY_THRESHOLD", 0.88)
    )

    # --- Server ---
    host: str = field(default_factory=lambda: os.getenv("PERSON1_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: _get_int("PERSON1_PORT", 8001))


settings = Settings()
