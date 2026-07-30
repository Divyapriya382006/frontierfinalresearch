"""
Minimal client for the public Papers with Code API (no key required).
Docs: https://paperswithcode.com/api/v1/docs/
"""
import logging
from typing import List, Dict, Any

import requests

from shared.utils.config import PAPERSWITHCODE_BASE_URL, REQUEST_TIMEOUT_SECONDS

logger = logging.getLogger("research_agent_x.pwc")


class PapersWithCodeClient:
    def __init__(self, base_url: str = PAPERSWITHCODE_BASE_URL, timeout: int = REQUEST_TIMEOUT_SECONDS):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def search_datasets(self, query: str, items_per_page: int = 20) -> List[Dict[str, Any]]:
        """
        Search datasets by free-text query (typically the research topic or task name).
        Returns a list of raw dataset dicts. Returns [] on any network/API failure
        instead of raising, so a flaky connection doesn't take down the whole pipeline.
        """
        url = f"{self.base_url}/datasets/"
        params = {"q": query, "items_per_page": items_per_page}
        try:
            resp = requests.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            if not isinstance(data, dict):
                return []
            return data.get("results", [])
        except (requests.RequestException, ValueError, TypeError) as exc:
            logger.warning("Papers with Code dataset search failed for %r: %s", query, exc)
            return []

    def search_papers_for_task(self, task: str, items_per_page: int = 20) -> List[Dict[str, Any]]:
        """Search papers tagged with a given task, useful for benchmark discovery."""
        url = f"{self.base_url}/papers/"
        params = {"q": task, "items_per_page": items_per_page}
        try:
            resp = requests.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            if not isinstance(data, dict):
                return []
            return data.get("results", [])
        except (requests.RequestException, ValueError, TypeError) as exc:
            logger.warning("Papers with Code paper search failed for %r: %s", task, exc)
            return []
