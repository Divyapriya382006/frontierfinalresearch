"""
person_1_literature_ranking/ranking/relevance_score.py

Computes semantic relevance between a search query and each paper using
TF-IDF + cosine similarity over the title+abstract text. This gives a
lightweight, dependency-cheap relevance signal without requiring an LLM
call or embedding API for every paper.
"""

import re
from typing import List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from shared.schemas.paper_schema import Paper
from shared.utils.helpers import normalize_text
from shared.utils.logger import get_logger

logger = get_logger(__name__)


class RelevanceScorer:
    """TF-IDF based relevance scorer, scoped to a single query's candidate set."""

    def __init__(self):
        self._vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_features=5000,
        )

    def score(self, query: str, papers: List[Paper]) -> List[Paper]:
        """Mutates and returns `papers` with `relevance_score` set in [0, 1]."""
        if not papers:
            return papers

        query_norm = normalize_text(query)
        query_terms = [term for term in re.split(r"\s+", query_norm) if term]
        documents = [query_norm] + [
            normalize_text(f"{p.title} {p.abstract}") for p in papers
        ]

        # Guard against a fully-empty corpus (e.g. every abstract missing)
        if not any(documents):
            for p in papers:
                p.relevance_score = 0.0
            return papers

        try:
            tfidf_matrix = self._vectorizer.fit_transform(documents)
        except ValueError:
            logger.warning("TF-IDF vectorization failed; defaulting relevance scores to 0")
            for p in papers:
                p.relevance_score = 0.0
            return papers

        query_vec = tfidf_matrix[0:1]
        paper_vecs = tfidf_matrix[1:]
        similarities = cosine_similarity(query_vec, paper_vecs).flatten()

        for paper, sim in zip(papers, similarities):
            base_score = float(max(0.0, min(1.0, sim)))
            title_text = (paper.title or "").lower()
            abstract_text = (paper.abstract or "").lower()
            combined_text = f"{title_text} {abstract_text}"

            exact_term_hits = sum(1 for term in query_terms if term and term in combined_text)
            phrase_hits = 1 if any(phrase in combined_text for phrase in ["large language model", "large language models", "llm", "gpt", "language model"]) else 0
            bonus = min(0.35, 0.08 * exact_term_hits + 0.12 * phrase_hits)
            paper.relevance_score = round(min(1.0, base_score + bonus), 4)

        return papers
