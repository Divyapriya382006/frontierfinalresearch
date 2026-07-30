"""
person_1_literature_ranking/ranking/score_calculator.py

Combines the individual signals (semantic relevance, citation count,
recency) into one final weighted score per paper, in [0, 1].
"""

import math
from typing import List

from shared.schemas.paper_schema import Paper
from shared.utils.config import settings
from shared.utils.helpers import years_since
from shared.utils.logger import get_logger

logger = get_logger(__name__)


class ScoreCalculator:
    def __init__(
        self,
        weight_relevance: float = None,
        weight_citations: float = None,
        weight_recency: float = None,
        weight_venue_quality: float = None,
    ):
        self.w_relevance = weight_relevance if weight_relevance is not None else settings.weight_relevance
        self.w_citations = weight_citations if weight_citations is not None else settings.weight_citations
        self.w_recency = weight_recency if weight_recency is not None else settings.weight_recency
        self.w_venue_quality = weight_venue_quality if weight_venue_quality is not None else settings.weight_venue_quality

    def _citation_score(self, papers: List[Paper]) -> None:
        """Log-scaled, min-max normalized citation count across the candidate set."""
        log_counts = [math.log1p(p.citation_count) for p in papers]
        max_log = max(log_counts) if log_counts else 0.0
        for paper, log_count in zip(papers, log_counts):
            paper.citation_score = round(log_count / max_log, 4) if max_log > 0 else 0.0

    def _recency_score(self, papers: List[Paper], half_life_years: float = 5.0) -> None:
        """Exponential decay: newer papers score closer to 1.0."""
        for paper in papers:
            age = years_since(paper.year)
            if age is None:
                paper.recency_score = 0.5  # unknown year -> neutral score
            else:
                paper.recency_score = round(math.exp(-age / half_life_years), 4)

    def _venue_quality_score(self, papers: List[Paper]) -> None:
        """Boost papers from well-known venues and suppress weak or unknown sources."""
        strong_venues = {
            "nature",
            "science",
            "pnas",
            "ieee",
            "acm",
            "nature machine intelligence",
            "communications medicine",
            "cell",
            "jmlr",
            "neurips",
            "iclr",
            "icml",
            "aaai",
        }
        for paper in papers:
            venue = (paper.venue or "").lower()
            if any(token in venue for token in strong_venues):
                paper.venue_quality_score = 1.0
            elif venue and "arxiv" not in venue:
                paper.venue_quality_score = 0.6
            else:
                paper.venue_quality_score = 0.3

    def calculate(self, papers: List[Paper]) -> List[Paper]:
        """Populate citation_score, recency_score, and final_score on each paper."""
        if not papers:
            return papers

        self._citation_score(papers)
        self._recency_score(papers)
        self._venue_quality_score(papers)

        for paper in papers:
            paper.final_score = round(
                self.w_relevance * paper.relevance_score
                + self.w_citations * paper.citation_score
                + self.w_recency * paper.recency_score
                + self.w_venue_quality * paper.venue_quality_score,
                4,
            )

        return papers
