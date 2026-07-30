from unittest.mock import MagicMock

from person_1_literature_ranking.services.literature_service import LiteratureService
from shared.schemas.paper_schema import Paper


def test_build_query_variants_expands_the_query():
    service = LiteratureService(fetcher=MagicMock())

    variants = service._build_query_variants("large language models")

    assert "large language models" in variants
    assert '"large language models"' in variants
    assert "LLM" in variants
    assert len(variants) >= 3


def test_search_papers_uses_multiple_query_variants():
    fetcher = MagicMock()
    fetcher.fetch_all.side_effect = [
        [Paper(title="Paper A", source="arxiv")],
        [Paper(title="Paper B", source="arxiv")],
        [Paper(title="Paper C", source="arxiv")],
        [Paper(title="Paper D", source="arxiv")],
        [Paper(title="Paper E", source="arxiv")],
        [Paper(title="Paper F", source="arxiv")],
    ]
    service = LiteratureService(fetcher=fetcher)

    papers = service.search_papers("large language models", limit_per_source=20, sources=["arxiv"])

    assert len(papers) == 6
    assert fetcher.fetch_all.call_count >= 2
