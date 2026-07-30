"""
person_1_literature_ranking/services/literature_service.py

Service layer wrapping PaperFetcher. This is the boundary the API routes
(and person 4's orchestrator) should call instead of touching the fetcher
directly - keeps API-specific error handling and logging in one place.
"""

import re
from typing import List, Optional

from shared.utils.config import settings

from shared.schemas.paper_schema import Paper
from shared.utils.logger import get_logger
from shared.utils.validators import validate_search_request, ValidationError

from person_1_literature_ranking.api.paper_fetcher import PaperFetcher

logger = get_logger(__name__)


class LiteratureService:
    def __init__(self, fetcher: Optional[PaperFetcher] = None):
        self.fetcher = fetcher or PaperFetcher()

    def search_papers(
        self,
        query: str,
        limit_per_source: Optional[int] = None,
        sources: Optional[List[str]] = None,
    ) -> List[Paper]:
        """Validate input and fetch raw papers using a small set of query variants."""
        payload = validate_search_request({"query": query, "top_k": 1, "sources": sources})
        variants = self._build_query_variants(payload["query"])

        effective_limit = limit_per_source or settings.max_results_per_source
        widened_limit = max(effective_limit, 20)

        papers: List[Paper] = []
        for variant in variants:
            fetched = self.fetcher.fetch_all(
                query=variant,
                limit_per_source=widened_limit,
                sources=payload["sources"],
            )
            papers.extend(fetched)

        filtered_papers = self._filter_by_year_and_terms(papers, payload["query"])
        unique_papers = self._dedup_papers(filtered_papers)
        logger.info(
            "LiteratureService fetched %d raw papers for query=%r using %d variants",
            len(unique_papers),
            query,
            len(variants),
        )
        return unique_papers

    def _build_query_variants(self, query: str) -> List[str]:
        cleaned = query.strip()
        if not cleaned:
            return []

        base = cleaned
        variants = [base, f'"{base}"', base.replace("large language models", "LLM")]
        if "large language models" in base.lower():
            variants.extend(["foundation models", "transformer language model", "generative AI"])
        return list(dict.fromkeys([v.strip() for v in variants if v and v.strip()]))

    @staticmethod
    def _filter_by_year_and_terms(papers: List[Paper], query: str) -> List[Paper]:
        """Drop clearly irrelevant papers using lightweight heuristics."""
        normalized_query = query.lower()
        min_year = 2020 if "large language models" in normalized_query or "llm" in normalized_query else 2018

        filtered: List[Paper] = []
        for paper in papers:
            if paper.year is not None and paper.year < min_year:
                continue
            text = " ".join([paper.title, paper.abstract, paper.venue or ""]).lower()
            if re.search(r"\b(medicine|healthcare|clinical|medical|drug discovery)\b", text) and "large language models" in normalized_query:
                if "medicine" in normalized_query or "healthcare" in normalized_query:
                    pass
                else:
                    continue
            filtered.append(paper)
        return filtered

    @staticmethod
    def _dedup_papers(papers: List[Paper]) -> List[Paper]:
        seen = set()
        unique: List[Paper] = []
        for paper in papers:
            key = paper.dedup_key()
            if key in seen:
                continue
            seen.add(key)
            unique.append(paper)
        return unique
