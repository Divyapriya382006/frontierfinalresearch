"""
person_1_literature_ranking/ranking/ranker.py

Top-level ranking pipeline: dedup -> relevance scoring -> weighted final
scoring -> sort -> truncate to top_k. This is the single entry point the
services layer (and orchestrator, in person 4) should call.
"""

from typing import List

from shared.schemas.paper_schema import Paper
from shared.utils.constants import DEFAULT_TOP_K
from shared.utils.logger import get_logger

from person_1_literature_ranking.ranking.duplicate_remover import DuplicateRemover
from person_1_literature_ranking.ranking.relevance_score import RelevanceScorer
from person_1_literature_ranking.ranking.score_calculator import ScoreCalculator

logger = get_logger(__name__)


class Ranker:
    def __init__(self):
        self.duplicate_remover = DuplicateRemover()
        self.relevance_scorer = RelevanceScorer()
        self.score_calculator = ScoreCalculator()

    def rank(self, query: str, papers: List[Paper], top_k: int = DEFAULT_TOP_K) -> List[Paper]:
        """
        Full ranking pipeline. Returns the top_k papers sorted by final_score
        descending.
        """
        if not papers:
            logger.info("No papers to rank for query=%r", query)
            return []

        deduped = self.duplicate_remover.remove_duplicates(papers)
        scored = self.relevance_scorer.score(query, deduped)
        finalized = self.score_calculator.calculate(scored)

        ranked = sorted(finalized, key=lambda p: p.final_score, reverse=True)
        top = ranked[:top_k]

        logger.info(
            "Ranked %d candidates (from %d raw) -> returning top %d",
            len(deduped),
            len(papers),
            len(top),
        )
        return top
