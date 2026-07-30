"""
person_1_literature_ranking/api/arxiv.py

Client for the arXiv API (Atom/XML based).
Docs: https://info.arxiv.org/help/api/user-manual.html
"""

import time
import xml.etree.ElementTree as ET
from typing import List

import requests

from shared.schemas.paper_schema import Paper
from shared.utils.config import settings
from shared.utils.constants import SOURCE_ARXIV, DEFAULT_USER_AGENT
from shared.utils.helpers import parse_year
from shared.utils.logger import get_logger

logger = get_logger(__name__)

ATOM_NS = "{http://www.w3.org/2005/Atom}"
ARXIV_NS = "{http://arxiv.org/schemas/atom}"


class ArxivClient:
    """Wrapper around the arXiv Atom search API."""

    def __init__(self):
        self.base_url = settings.arxiv_base_url
        self.timeout = settings.request_timeout_seconds
        self.max_retries = settings.max_retries
        self.headers = {"User-Agent": DEFAULT_USER_AGENT}

    def search(self, query: str, limit: int = 20) -> List[Paper]:
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": limit,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = requests.get(self.base_url, params=params, headers=self.headers, timeout=self.timeout)
                resp.raise_for_status()
                return self._parse_feed(resp.text)
            except (requests.RequestException, ET.ParseError) as exc:
                logger.warning("arXiv request failed (attempt %d/%d): %s", attempt, self.max_retries, exc)
                time.sleep(settings.retry_backoff_seconds * attempt)

        logger.error("arXiv search failed for query=%r after %d attempts", query, self.max_retries)
        return []

    def _parse_feed(self, xml_text: str) -> List[Paper]:
        root = ET.fromstring(xml_text)
        papers = []
        for entry in root.findall(f"{ATOM_NS}entry"):
            papers.append(self._to_paper(entry))
        return papers

    @staticmethod
    def _to_paper(entry: ET.Element) -> Paper:
        def text(tag: str, ns: str = ATOM_NS) -> str:
            el = entry.find(f"{ns}{tag}")
            return el.text.strip() if el is not None and el.text else ""

        title = " ".join(text("title").split())
        abstract = " ".join(text("summary").split())
        published = text("published")

        authors = [
            (a.find(f"{ATOM_NS}name").text or "").strip()
            for a in entry.findall(f"{ATOM_NS}author")
            if a.find(f"{ATOM_NS}name") is not None
        ]

        arxiv_id = text("id")  # e.g. http://arxiv.org/abs/2101.01234v1
        pdf_url = None
        abs_url = arxiv_id
        for link in entry.findall(f"{ATOM_NS}link"):
            if link.get("title") == "pdf":
                pdf_url = link.get("href")

        primary_category_el = entry.find(f"{ARXIV_NS}primary_category")
        field_of_study = (
            [primary_category_el.get("term")] if primary_category_el is not None else []
        )

        return Paper(
            title=title,
            abstract=abstract,
            authors=authors,
            year=parse_year(published),
            venue="arXiv preprint",
            url=abs_url,
            pdf_url=pdf_url,
            doi=None,
            source=SOURCE_ARXIV,
            source_id=arxiv_id,
            citation_count=0,  # arXiv API does not expose citation counts
            fields_of_study=field_of_study,
        )
