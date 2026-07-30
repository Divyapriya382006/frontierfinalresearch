"""
person_1_literature_ranking/api/tavily.py

Client for Tavily web search results.

This wraps the Tavily search API and normalizes web snippets into the shared
Paper schema so they can be ranked alongside academic sources.
"""

import time
from typing import List

import requests

from shared.schemas.paper_schema import Paper
from shared.utils.config import settings
from shared.utils.constants import DEFAULT_USER_AGENT, SOURCE_TAVILY
from shared.utils.logger import get_logger

logger = get_logger(__name__)


class TavilyClient:
    """Wrapper around the Tavily search API."""

    def __init__(self, api_key: str | None = None):
        self.base_url = settings.tavily_base_url
        self.api_key = api_key or settings.tavily_api_key
        self.timeout = settings.request_timeout_seconds
        self.max_retries = settings.max_retries
        self.headers = {
            "User-Agent": DEFAULT_USER_AGENT,
            "Content-Type": "application/json",
        }

    def search(self, query: str, limit: int = 10) -> List[Paper]:
        if not self.api_key:
            logger.info("Tavily API key not configured; returning no web results")
            return []

        payload = {"query": query, "search_depth": "basic", "max_results": min(limit, 10)}
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = requests.post(
                    self.base_url,
                    json=payload,
                    headers={**self.headers, "Authorization": f"Bearer {self.api_key}"},
                    timeout=self.timeout,
                )
                resp.raise_for_status()
                data = resp.json()
                return [self._to_paper(item) for item in data.get("results", [])]
            except requests.RequestException as exc:
                logger.warning("Tavily request failed (attempt %d/%d): %s", attempt, self.max_retries, exc)
                time.sleep(settings.retry_backoff_seconds * attempt)

        logger.error("Tavily search failed for query=%r after %d attempts", query, self.max_retries)
        return []

    @staticmethod
    def _to_paper(item: dict) -> Paper:
        return Paper(
            title=item.get("title") or "Untitled web result",
            abstract=item.get("content") or "",
            authors=[],
            year=None,
            venue="Web",
            url=item.get("url"),
            pdf_url=None,
            doi=None,
            source=SOURCE_TAVILY,
            source_id=item.get("url") or item.get("title") or "",
            citation_count=0,
            fields_of_study=[],
        )
