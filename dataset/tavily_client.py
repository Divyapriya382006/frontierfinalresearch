"""
Minimal client for the Tavily search API (https://tavily.com).
This is a web-search API purpose-built for AI agents - it crawls and
returns clean results server-side, so we don't need to scrape/parse HTML
ourselves. Useful for finding datasets that live outside Kaggle/Papers with
Code (government portals, university pages, GitHub repos, etc).
"""
import logging
from typing import List, Dict, Any

import requests

from shared.utils.config import TAVILY_API_KEY, TAVILY_BASE_URL, REQUEST_TIMEOUT_SECONDS

logger = logging.getLogger("research_agent_x.tavily")


class TavilyClient:
    def __init__(
        self,
        api_key: str = TAVILY_API_KEY,
        base_url: str = TAVILY_BASE_URL,
        timeout: int = REQUEST_TIMEOUT_SECONDS,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def search_datasets(self, topic: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search the web for datasets relevant to a research topic. Returns []
        (never raises) if no API key is configured or the request fails.
        """
        if not self.is_configured:
            logger.info("TAVILY_API_KEY not set; skipping Tavily search.")
            return []

        query = f"{topic} dataset for research"
        try:
            resp = requests.post(
                f"{self.base_url}/search",
                json={
                    "api_key": self.api_key,
                    "query": query,
                    "search_depth": "basic",
                    "max_results": max_results,
                    "include_answer": False,
                },
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("results", [])
        except requests.RequestException as exc:
            logger.warning("Tavily search failed for %r: %s", topic, exc)
            return []
