"""
person_1_literature_ranking/api/openalex.py

Client for the OpenAlex Works API.
Docs: https://docs.openalex.org/api-entities/works
"""

import time
from typing import List

import requests

from shared.schemas.paper_schema import Paper
from shared.utils.config import settings
from shared.utils.constants import SOURCE_OPENALEX, DEFAULT_USER_AGENT
from shared.utils.helpers import safe_int
from shared.utils.logger import get_logger

logger = get_logger(__name__)


class OpenAlexClient:
    """Wrapper around the OpenAlex /works search endpoint."""

    def __init__(self):
        self.base_url = settings.openalex_base_url
        self.timeout = settings.request_timeout_seconds
        self.max_retries = settings.max_retries
        self.headers = {"User-Agent": DEFAULT_USER_AGENT}

    def search(self, query: str, limit: int = 20) -> List[Paper]:
        url = f"{self.base_url}/works"
        params = {"search": query, "per_page": min(limit, 50)}
        if settings.openalex_mailto:
            params["mailto"] = settings.openalex_mailto

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = requests.get(url, params=params, headers=self.headers, timeout=self.timeout)
                if resp.status_code == 429:
                    wait = settings.retry_backoff_seconds * attempt
                    logger.warning("OpenAlex rate limited, retrying in %.1fs", wait)
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                data = resp.json()
                return [self._to_paper(item) for item in data.get("results", [])]
            except requests.RequestException as exc:
                logger.warning("OpenAlex request failed (attempt %d/%d): %s", attempt, self.max_retries, exc)
                time.sleep(settings.retry_backoff_seconds * attempt)

        logger.error("OpenAlex search failed for query=%r after %d attempts", query, self.max_retries)
        return []

    @staticmethod
    def _reconstruct_abstract(inverted_index: dict) -> str:
        """OpenAlex stores abstracts as an inverted index {word: [positions]}."""
        if not inverted_index:
            return ""
        position_map = {}
        for word, positions in inverted_index.items():
            for pos in positions:
                position_map[pos] = word
        if not position_map:
            return ""
        max_pos = max(position_map.keys())
        return " ".join(position_map.get(i, "") for i in range(max_pos + 1)).strip()

    @classmethod
    def _to_paper(cls, item: dict) -> Paper:
        authors = [
            (a.get("author") or {}).get("display_name", "")
            for a in (item.get("authorships") or [])
            if (a.get("author") or {}).get("display_name")
        ]
        primary_location = item.get("primary_location") or {}
        source_info = primary_location.get("source") or {}
        best_oa = item.get("best_oa_location") or {}
        concepts = [c.get("display_name") for c in (item.get("concepts") or [])[:5] if c.get("display_name")]

        return Paper(
            title=item.get("title") or item.get("display_name") or "",
            abstract=cls._reconstruct_abstract(item.get("abstract_inverted_index")),
            authors=authors,
            year=item.get("publication_year"),
            venue=source_info.get("display_name"),
            url=item.get("id"),
            pdf_url=best_oa.get("pdf_url") or primary_location.get("pdf_url"),
            doi=(item.get("doi") or "").replace("https://doi.org/", "") or None,
            source=SOURCE_OPENALEX,
            source_id=item.get("id", ""),
            citation_count=safe_int(item.get("cited_by_count"), 0),
            fields_of_study=concepts,
        )
