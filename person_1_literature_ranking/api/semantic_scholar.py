"""
person_1_literature_ranking/api/semantic_scholar.py

Client for the Semantic Scholar Graph API.
Docs: https://api.semanticscholar.org/api-docs/graph
"""

import time
from typing import List

import requests

from shared.schemas.paper_schema import Paper
from shared.utils.config import settings
from shared.utils.constants import SOURCE_SEMANTIC_SCHOLAR, DEFAULT_USER_AGENT
from shared.utils.helpers import parse_year, safe_int
from shared.utils.logger import get_logger

logger = get_logger(__name__)

FIELDS = ",".join(
    [
        "title",
        "abstract",
        "authors",
        "year",
        "venue",
        "url",
        "openAccessPdf",
        "externalIds",
        "citationCount",
        "fieldsOfStudy",
    ]
)


class SemanticScholarClient:
    """Thin, retrying wrapper around the Semantic Scholar search endpoint."""

    def __init__(self):
        self.base_url = settings.semantic_scholar_base_url
        self.timeout = settings.request_timeout_seconds
        self.max_retries = settings.max_retries
        self.headers = {"User-Agent": DEFAULT_USER_AGENT}
        if settings.semantic_scholar_api_key:
            self.headers["x-api-key"] = settings.semantic_scholar_api_key

    def search(self, query: str, limit: int = 20) -> List[Paper]:
        """Search papers by keyword query and return normalized Paper objects."""
        url = f"{self.base_url}/paper/search"
        params = {"query": query, "limit": limit, "fields": FIELDS}

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = requests.get(url, params=params, headers=self.headers, timeout=self.timeout)
                if resp.status_code == 429:
                    wait = settings.retry_backoff_seconds * attempt
                    logger.warning("Semantic Scholar rate limited, retrying in %.1fs", wait)
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                data = resp.json()
                return [self._to_paper(item) for item in data.get("data", [])]
            except requests.RequestException as exc:
                logger.warning(
                    "Semantic Scholar request failed (attempt %d/%d): %s",
                    attempt,
                    self.max_retries,
                    exc,
                )
                time.sleep(settings.retry_backoff_seconds * attempt)

        logger.error("Semantic Scholar search failed for query=%r after %d attempts", query, self.max_retries)
        return []

    @staticmethod
    def _to_paper(item: dict) -> Paper:
        authors = [a.get("name", "") for a in (item.get("authors") or []) if a.get("name")]
        pdf_info = item.get("openAccessPdf") or {}
        external_ids = item.get("externalIds") or {}

        return Paper(
            title=item.get("title") or "",
            abstract=item.get("abstract") or "",
            authors=authors,
            year=item.get("year") or parse_year(item.get("year")),
            venue=item.get("venue"),
            url=item.get("url"),
            pdf_url=pdf_info.get("url"),
            doi=external_ids.get("DOI"),
            source=SOURCE_SEMANTIC_SCHOLAR,
            source_id=str(external_ids.get("DOI") or item.get("paperId", "")),
            citation_count=safe_int(item.get("citationCount"), 0),
            fields_of_study=item.get("fieldsOfStudy") or [],
        )
