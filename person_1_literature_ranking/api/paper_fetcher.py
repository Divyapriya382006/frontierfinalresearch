"""
person_1_literature_ranking/api/paper_fetcher.py

Aggregates results from all literature sources (Semantic Scholar, arXiv,
OpenAlex) concurrently and returns one flat, normalized list of Paper
objects for downstream ranking.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional

from shared.schemas.paper_schema import Paper
from shared.utils.config import settings
from shared.utils.constants import (
    SOURCE_SEMANTIC_SCHOLAR,
    SOURCE_ARXIV,
    SOURCE_OPENALEX,
    SOURCE_GOOGLE_SCHOLAR,
    SOURCE_TAVILY,
    ALL_SOURCES,
)
from shared.utils.logger import get_logger

from person_1_literature_ranking.api.semantic_scholar import SemanticScholarClient
from person_1_literature_ranking.api.arxiv import ArxivClient
from person_1_literature_ranking.api.openalex import OpenAlexClient
from person_1_literature_ranking.api.google_scholar import GoogleScholarClient
from person_1_literature_ranking.api.tavily import TavilyClient

logger = get_logger(__name__)


class PaperFetcher:
    """Fan-out fetcher that queries multiple academic APIs in parallel."""

    def __init__(self):
        self._clients = {
            SOURCE_SEMANTIC_SCHOLAR: SemanticScholarClient(),
            SOURCE_ARXIV: ArxivClient(),
            SOURCE_OPENALEX: OpenAlexClient(),
            SOURCE_GOOGLE_SCHOLAR: GoogleScholarClient(),
            SOURCE_TAVILY: TavilyClient(),
        }

    def fetch_all(
        self,
        query: str,
        limit_per_source: Optional[int] = None,
        sources: Optional[List[str]] = None,
    ) -> List[Paper]:
        """
        Fetch papers matching `query` from all requested sources concurrently.

        Args:
            query: free-text search query (e.g. a research topic).
            limit_per_source: max results to request from each individual API.
            sources: subset of ALL_SOURCES to query; defaults to all of them.

        Returns:
            Flat list of Paper objects (not deduped/ranked yet).
        """
        limit = limit_per_source or settings.max_results_per_source
        active_sources = sources or ALL_SOURCES
        invalid = set(active_sources) - set(ALL_SOURCES)
        if invalid:
            logger.warning("Ignoring unknown sources: %s", invalid)
        active_sources = [s for s in active_sources if s in ALL_SOURCES]

        results: List[Paper] = []
        with ThreadPoolExecutor(max_workers=len(active_sources) or 1) as executor:
            future_to_source = {
                executor.submit(self._clients[src].search, query, limit): src
                for src in active_sources
            }
            for future in as_completed(future_to_source):
                src = future_to_source[future]
                try:
                    papers = future.result()
                    logger.info("Fetched %d papers from %s", len(papers), src)
                    results.extend(papers)
                except Exception as exc:  # noqa: BLE001 - log and continue with other sources
                    logger.error("Source %s raised an exception: %s", src, exc)

        # Drop papers with no usable title/abstract - not useful for ranking
        results = [p for p in results if p.title.strip()]
        return results
