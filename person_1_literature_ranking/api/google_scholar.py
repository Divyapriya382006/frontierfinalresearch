"""
person_1_literature_ranking/api/google_scholar.py

Client for Google Scholar search results.

This uses the public Scholar HTML endpoint and extracts basic metadata from
search result snippets. It is intentionally lightweight and resilient to
missing structure so the rest of the pipeline can continue even when Google
returns an unexpected page layout.
"""

import html
import re
import time
from typing import List

import requests

from shared.schemas.paper_schema import Paper
from shared.utils.config import settings
from shared.utils.constants import DEFAULT_USER_AGENT, SOURCE_GOOGLE_SCHOLAR
from shared.utils.helpers import parse_year
from shared.utils.logger import get_logger

logger = get_logger(__name__)


class GoogleScholarClient:
    """Wrapper around the public Google Scholar HTML search page."""

    def __init__(self):
        self.base_url = settings.google_scholar_base_url
        self.timeout = settings.request_timeout_seconds
        self.max_retries = settings.max_retries
        self.headers = {
            "User-Agent": DEFAULT_USER_AGENT,
            "Accept-Language": "en-US,en;q=0.9",
        }

    def search(self, query: str, limit: int = 10) -> List[Paper]:
        params = {"q": query, "hl": "en", "num": min(limit, 20)}

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = requests.get(self.base_url, params=params, headers=self.headers, timeout=self.timeout)
                resp.raise_for_status()
                return self._parse_html(resp.text)
            except requests.RequestException as exc:
                logger.warning("Google Scholar request failed (attempt %d/%d): %s", attempt, self.max_retries, exc)
                time.sleep(settings.retry_backoff_seconds * attempt)

        logger.error("Google Scholar search failed for query=%r after %d attempts", query, self.max_retries)
        return []

    def _parse_html(self, html_text: str) -> List[Paper]:
        papers: List[Paper] = []
        for match in re.finditer(r"<h3[^>]*class=['\"][^'\"]*gs_rt[^'\"]*['\"][^>]*>(.*?)</h3>", html_text, re.I | re.S):
            block = match.group(1)
            title_match = re.search(r"<a[^>]+href=['\"]([^'\"]+)['\"][^>]*>(.*?)</a>", block, re.I | re.S)
            if not title_match:
                continue

            title = self._clean_text(title_match.group(2))
            url = title_match.group(1)
            abstract = ""
            abstract_match = re.search(r"<div[^>]*class=['\"][^'\"]*gs_rs[^'\"]*['\"][^>]*>(.*?)</div>", html_text, re.I | re.S)
            if abstract_match:
                abstract = self._clean_text(abstract_match.group(1))

            author_text = ""
            author_match = re.search(r"<div[^>]*class=['\"][^'\"]*gs_a[^'\"]*['\"][^>]*>(.*?)</div>", html_text, re.I | re.S)
            if author_match:
                author_text = self._clean_text(author_match.group(1))

            year = parse_year(author_text)
            authors = [item.strip() for item in author_text.split(" - ")[0].split(",") if item.strip()]
            papers.append(
                Paper(
                    title=title,
                    abstract=abstract,
                    authors=authors[:5],
                    year=year,
                    venue=None,
                    url=url,
                    pdf_url=None,
                    doi=None,
                    source=SOURCE_GOOGLE_SCHOLAR,
                    source_id=url,
                    citation_count=0,
                    fields_of_study=[],
                )
            )
            if len(papers) >= 10:
                break
        return papers

    @staticmethod
    def _clean_text(value: str) -> str:
        text = html.unescape(re.sub(r"<[^>]+>", " ", value))
        return " ".join(text.split())
