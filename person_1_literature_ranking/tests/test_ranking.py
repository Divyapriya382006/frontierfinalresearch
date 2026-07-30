"""
person_1_literature_ranking/tests/test_ranking.py

Unit tests for the ranking pipeline: relevance scoring, duplicate removal,
score calculation, and the full Ranker.
"""

import pytest

from shared.schemas.paper_schema import Paper
from person_1_literature_ranking.ranking.relevance_score import RelevanceScorer
from person_1_literature_ranking.ranking.duplicate_remover import DuplicateRemover
from person_1_literature_ranking.ranking.score_calculator import ScoreCalculator
from person_1_literature_ranking.ranking.ranker import Ranker


def make_paper(title, abstract="", year=2023, citation_count=0, doi=None, source="test"):
    return Paper(
        title=title,
        abstract=abstract,
        authors=["A. Author"],
        year=year,
        citation_count=citation_count,
        doi=doi,
        source=source,
        source_id=title,
    )


class TestRelevanceScorer:
    def test_scores_are_in_valid_range(self):
        papers = [
            make_paper("Graph Neural Networks for Drug Discovery", "GNNs applied to molecules"),
            make_paper("Cooking pasta the Italian way", "A recipe guide"),
        ]
        scorer = RelevanceScorer()
        scored = scorer.score("graph neural networks drug discovery", papers)
        for p in scored:
            assert 0.0 <= p.relevance_score <= 1.0

    def test_more_relevant_paper_scores_higher(self):
        relevant = make_paper("Graph Neural Networks for Drug Discovery", "GNNs applied to molecules")
        irrelevant = make_paper("Cooking pasta the Italian way", "A recipe guide for beginners")
        scorer = RelevanceScorer()
        scored = scorer.score("graph neural networks drug discovery", [relevant, irrelevant])
        scored_map = {p.title: p.relevance_score for p in scored}
        assert scored_map[relevant.title] > scored_map[irrelevant.title]

    def test_empty_paper_list(self):
        scorer = RelevanceScorer()
        assert scorer.score("anything", []) == []


class TestDuplicateRemover:
    def test_removes_exact_doi_duplicates(self):
        p1 = make_paper("Attention Is All You Need", doi="10.5555/attn", source="arxiv")
        p2 = make_paper("Attention is all you need", doi="10.5555/attn", source="semantic_scholar")
        remover = DuplicateRemover()
        result = remover.remove_duplicates([p1, p2])
        assert len(result) == 1

    def test_removes_near_duplicate_titles(self):
        p1 = make_paper("Deep Residual Learning for Image Recognition")
        p2 = make_paper("Deep Residual Learning for Image Recognition.")
        remover = DuplicateRemover(similarity_threshold=0.9)
        result = remover.remove_duplicates([p1, p2])
        assert len(result) == 1

    def test_keeps_distinct_papers(self):
        p1 = make_paper("Transformers for NLP")
        p2 = make_paper("Convolutional Networks for Vision")
        remover = DuplicateRemover()
        result = remover.remove_duplicates([p1, p2])
        assert len(result) == 2

    def test_prefers_richer_metadata_on_duplicate(self):
        sparse = make_paper("BERT Pretraining", abstract="", citation_count=0, doi="10.1/bert")
        rich = make_paper("BERT Pretraining", abstract="A detailed abstract.", citation_count=500, doi="10.1/bert")
        remover = DuplicateRemover()
        result = remover.remove_duplicates([sparse, rich])
        assert len(result) == 1
        assert result[0].citation_count == 500


class TestScoreCalculator:
    def test_final_score_is_weighted_combination(self):
        papers = [make_paper("Paper A", year=2024, citation_count=100)]
        papers[0].relevance_score = 0.8
        calc = ScoreCalculator(weight_relevance=0.5, weight_citations=0.3, weight_recency=0.2)
        result = calc.calculate(papers)
        assert 0.0 <= result[0].final_score <= 1.0

    def test_higher_citations_yield_higher_citation_score(self):
        low = make_paper("Low citations", citation_count=1)
        high = make_paper("High citations", citation_count=10000)
        calc = ScoreCalculator()
        result = calc.calculate([low, high])
        by_title = {p.title: p.citation_score for p in result}
        assert by_title["High citations"] > by_title["Low citations"]

    def test_recent_paper_scores_higher_than_old(self):
        recent = make_paper("Recent", year=2025)
        old = make_paper("Old", year=1995)
        calc = ScoreCalculator()
        result = calc.calculate([recent, old])
        by_title = {p.title: p.recency_score for p in result}
        assert by_title["Recent"] > by_title["Old"]

    def test_handles_empty_list(self):
        calc = ScoreCalculator()
        assert calc.calculate([]) == []


class TestRanker:
    def test_full_pipeline_returns_sorted_top_k(self):
        papers = [
            make_paper("Graph Neural Networks Survey", "A survey of GNNs", year=2023, citation_count=50),
            make_paper("Unrelated Cooking Guide", "How to cook rice", year=2010, citation_count=2),
            make_paper("Deep Learning for Molecules", "GNN based molecule modeling", year=2024, citation_count=120),
        ]
        ranker = Ranker()
        ranked = ranker.rank("graph neural networks molecules", papers, top_k=2)

        assert len(ranked) == 2
        # Results should be sorted descending by final_score
        assert ranked[0].final_score >= ranked[1].final_score

    def test_empty_input_returns_empty_list(self):
        ranker = Ranker()
        assert ranker.rank("anything", [], top_k=10) == []

    def test_deduplicates_before_ranking(self):
        p1 = make_paper("Same Paper", doi="10.1/x")
        p2 = make_paper("Same Paper", doi="10.1/x")
        ranker = Ranker()
        ranked = ranker.rank("same paper", [p1, p2], top_k=10)
        assert len(ranked) == 1
