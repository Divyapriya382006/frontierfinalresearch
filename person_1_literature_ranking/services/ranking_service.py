"""
person_1_literature_ranking/services/ranking_service.py

Highest-level service for Person 1's module: fetch -> rank -> (optionally)
persist to outputs/papers.json. This is what main.py (CLI/API) and the
orchestrator (person 4) call for the full end-to-end literature search.
"""

import json
from pathlib import Path
from typing import List, Optional

from shared.schemas.paper_schema import Paper
from shared.utils.constants import DEFAULT_TOP_K, DEFAULT_OUTPUT_FILENAME
from shared.utils.logger import get_logger
from shared.utils.validators import validate_search_request

from person_1_literature_ranking.ranking.ranker import Ranker
from person_1_literature_ranking.services.literature_service import LiteratureService

logger = get_logger(__name__)

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs"


class RankingService:
    def __init__(
        self,
        literature_service: Optional[LiteratureService] = None,
        ranker: Optional[Ranker] = None,
    ):
        self.literature_service = literature_service or LiteratureService()
        self.ranker = ranker or Ranker()

    def search_and_rank(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        sources: Optional[List[str]] = None,
        limit_per_source: Optional[int] = None,
        min_year: Optional[int] = None,
        save: bool = False,
        output_filename: str = DEFAULT_OUTPUT_FILENAME,
    ) -> List[Paper]:
        """
        End-to-end: fetch candidate papers from all sources, dedup, score,
        rank, and return the top_k. Optionally persist to disk as JSON so
        downstream agents (summary/gap, dataset/planner) can consume it.
        """
        validated = validate_search_request({"query": query, "top_k": top_k, "sources": sources})

        raw_papers = self.literature_service.search_papers(
            query=validated["query"],
            limit_per_source=limit_per_source,
            sources=validated["sources"],
        )

        if min_year is not None:
            raw_papers = [paper for paper in raw_papers if paper.year is None or paper.year >= min_year]

        raw_papers = [paper for paper in raw_papers if getattr(paper, "relevance_score", 0.0) >= 0.05]

        ranked_papers = self.ranker.rank(validated["query"], raw_papers, top_k=validated["top_k"])

        if save:
            self._save(ranked_papers, output_filename)

        return ranked_papers

    def _save(self, papers: List[Paper], filename: str) -> Path:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = OUTPUT_DIR / filename
        with out_path.open("w", encoding="utf-8") as f:
            json.dump([p.to_dict() for p in papers], f, indent=2, ensure_ascii=False)
        logger.info("Saved %d ranked papers to %s", len(papers), out_path)
        return out_path
