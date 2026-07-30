"""
Minimal client for the Kaggle public API's dataset search endpoint.
Docs: https://www.kaggle.com/docs/api

Auth: Kaggle uses HTTP Basic Auth with your username + API key (get one at
https://www.kaggle.com/settings/account -> "Create New Token", which
downloads a kaggle.json containing {"username": "...", "key": "..."}).
"""
import logging
from typing import List, Dict, Any

import requests
from requests.auth import HTTPBasicAuth

from shared.utils.config import KAGGLE_USERNAME, KAGGLE_KEY, KAGGLE_BASE_URL, REQUEST_TIMEOUT_SECONDS

logger = logging.getLogger("research_agent_x.kaggle")


class KaggleClient:
    def __init__(
        self,
        username: str = KAGGLE_USERNAME,
        key: str = KAGGLE_KEY,
        base_url: str = KAGGLE_BASE_URL,
        timeout: int = REQUEST_TIMEOUT_SECONDS,
    ):
        self.username = username
        self.key = key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    @property
    def is_configured(self) -> bool:
        return bool(self.username and self.key)

    def search_datasets(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Search Kaggle datasets by free-text query. Returns [] (never raises)
        if credentials are missing or the request fails, so a missing/bad
        Kaggle key just means "no Kaggle results", not a crash.
        """
        if not self.is_configured:
            logger.info("KAGGLE_USERNAME/KAGGLE_KEY not set; skipping Kaggle search.")
            return []

        url = f"{self.base_url}/datasets/list"
        params = {"search": query, "pageSize": max_results, "sortBy": "relevance"}
        try:
            resp = requests.get(
                url,
                params=params,
                auth=HTTPBasicAuth(self.username, self.key),
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            logger.warning("Kaggle dataset search failed for %r: %s", query, exc)
            return []
