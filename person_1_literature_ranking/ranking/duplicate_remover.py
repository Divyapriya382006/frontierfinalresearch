"""
person_1_literature_ranking/ranking/duplicate_remover.py

Removes duplicate papers that were returned by more than one source
(a very common occurrence, e.g. a paper on both arXiv and Semantic Scholar).

Strategy:
  1. Exact-match pass on normalized DOI / normalized title (cheap, catches most dupes).
  2. Fuzzy pass using SequenceMatcher on normalized titles for near-duplicates
     (e.g. minor punctuation/casing differences between sources).
When a duplicate is found, we keep the version with the richer metadata
(prefer non-empty abstract, then higher citation count).
"""

from difflib import SequenceMatcher
from typing import List

from shared.schemas.paper_schema import Paper
from shared.utils.config import settings
from shared.utils.helpers import normalize_text
from shared.utils.logger import get_logger

logger = get_logger(__name__)


def _richer(a: Paper, b: Paper) -> Paper:
    """Return whichever of two duplicate papers has more useful metadata."""
    a_score = (len(a.abstract or ""), a.citation_count)
    b_score = (len(b.abstract or ""), b.citation_count)
    return a if a_score >= b_score else b


class DuplicateRemover:
    def __init__(self, similarity_threshold: float = None):
        self.similarity_threshold = similarity_threshold or settings.duplicate_similarity_threshold

    def remove_duplicates(self, papers: List[Paper]) -> List[Paper]:
        # --- Pass 1: exact-match dedup on DOI / normalized title ---
        exact_map = {}
        for paper in papers:
            key = paper.dedup_key()
            if key in exact_map:
                exact_map[key] = _richer(exact_map[key], paper)
            else:
                exact_map[key] = paper

        deduped = list(exact_map.values())

        # --- Pass 2: fuzzy title matching for near-duplicates across sources ---
        final: List[Paper] = []
        used = [False] * len(deduped)
        norm_titles = [normalize_text(p.title) for p in deduped]

        for i, paper in enumerate(deduped):
            if used[i]:
                continue
            best = paper
            used[i] = True
            for j in range(i + 1, len(deduped)):
                if used[j]:
                    continue
                similarity = SequenceMatcher(None, norm_titles[i], norm_titles[j]).ratio()
                if similarity >= self.similarity_threshold:
                    best = _richer(best, deduped[j])
                    used[j] = True
            final.append(best)

        removed_count = len(papers) - len(final)
        if removed_count:
            logger.info("Removed %d duplicate paper(s) out of %d", removed_count, len(papers))

        return final
