"""
person_1_literature_ranking/tests/test_fetcher.py

Tests for the source clients (Semantic Scholar, arXiv, OpenAlex) and the
aggregating PaperFetcher. External HTTP calls are mocked so tests run
offline and deterministically.
"""

from unittest.mock import patch, MagicMock

from person_1_literature_ranking.api.semantic_scholar import SemanticScholarClient
from person_1_literature_ranking.api.openalex import OpenAlexClient
from person_1_literature_ranking.api.google_scholar import GoogleScholarClient
from person_1_literature_ranking.api.tavily import TavilyClient
from person_1_literature_ranking.api.paper_fetcher import PaperFetcher


SEMANTIC_SCHOLAR_RESPONSE = {
    "data": [
        {
            "title": "Graph Neural Networks for Molecules",
            "abstract": "We study GNNs applied to molecular graphs.",
            "authors": [{"name": "Jane Doe"}],
            "year": 2023,
            "venue": "NeurIPS",
            "url": "https://semanticscholar.org/paper/123",
            "openAccessPdf": {"url": "https://example.com/paper.pdf"},
            "externalIds": {"DOI": "10.1234/abc"},
            "citationCount": 42,
            "fieldsOfStudy": ["Computer Science"],
        }
    ]
}

OPENALEX_RESPONSE = {
    "results": [
        {
            "title": "Molecular Property Prediction",
            "display_name": "Molecular Property Prediction",
            "abstract_inverted_index": {"We": [0], "predict": [1], "properties": [2]},
            "authorships": [{"author": {"display_name": "John Smith"}}],
            "publication_year": 2022,
            "primary_location": {"source": {"display_name": "Journal of Chem Info"}},
            "best_oa_location": {"pdf_url": "https://example.com/oa.pdf"},
            "id": "https://openalex.org/W123",
            "doi": "https://doi.org/10.5678/xyz",
            "cited_by_count": 10,
            "concepts": [{"display_name": "Chemistry"}],
        }
    ]
}


class TestSemanticScholarClient:
    @patch("person_1_literature_ranking.api.semantic_scholar.requests.get")
    def test_search_parses_response_into_papers(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = SEMANTIC_SCHOLAR_RESPONSE
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        client = SemanticScholarClient()
        papers = client.search("graph neural networks", limit=5)

        assert len(papers) == 1
        assert papers[0].title == "Graph Neural Networks for Molecules"
        assert papers[0].citation_count == 42
        assert papers[0].doi == "10.1234/abc"
        assert papers[0].source == "semantic_scholar"

    @patch("person_1_literature_ranking.api.semantic_scholar.requests.get")
    def test_search_returns_empty_list_on_repeated_failure(self, mock_get):
        mock_get.side_effect = Exception("network down")
        client = SemanticScholarClient()
        # requests.RequestException is what's caught; generic Exception will
        # propagate, so simulate the real exception type instead.
        import requests

        mock_get.side_effect = requests.RequestException("boom")
        papers = client.search("query", limit=5)
        assert papers == []


class TestOpenAlexClient:
    @patch("person_1_literature_ranking.api.openalex.requests.get")
    def test_search_parses_response_and_reconstructs_abstract(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = OPENALEX_RESPONSE
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        client = OpenAlexClient()
        papers = client.search("molecular properties", limit=5)

        assert len(papers) == 1
        assert papers[0].title == "Molecular Property Prediction"
        assert papers[0].abstract == "We predict properties"
        assert papers[0].doi == "10.5678/xyz"
        assert papers[0].citation_count == 10


class TestPaperFetcher:
    @patch.object(SemanticScholarClient, "search")
    @patch("person_1_literature_ranking.api.paper_fetcher.ArxivClient")
    @patch.object(OpenAlexClient, "search")
    @patch.object(GoogleScholarClient, "search")
    @patch.object(TavilyClient, "search")
    def test_fetch_all_aggregates_sources(
        self,
        mock_tavily_search,
        mock_google_scholar_search,
        mock_openalex_search,
        mock_arxiv_cls,
        mock_ss_search,
    ):
        from shared.schemas.paper_schema import Paper

        mock_ss_search.return_value = [Paper(title="SS Paper", source="semantic_scholar")]
        mock_openalex_search.return_value = [Paper(title="OA Paper", source="openalex")]
        mock_google_scholar_search.return_value = [Paper(title="GS Paper", source="google_scholar")]
        mock_tavily_search.return_value = [Paper(title="Tavily Paper", source="tavily")]
        mock_arxiv_instance = MagicMock()
        mock_arxiv_instance.search.return_value = [Paper(title="Arxiv Paper", source="arxiv")]
        mock_arxiv_cls.return_value = mock_arxiv_instance

        fetcher = PaperFetcher()
        fetcher._clients["arxiv"] = mock_arxiv_instance

        results = fetcher.fetch_all("test query", limit_per_source=5)
        titles = {p.title for p in results}

        assert "SS Paper" in titles
        assert "OA Paper" in titles
        assert "GS Paper" in titles
        assert "Tavily Paper" in titles
        assert "Arxiv Paper" in titles
        assert len(results) == 5

    def test_fetch_all_filters_unknown_sources(self):
        fetcher = PaperFetcher()
        # Should not raise, just ignore unknown source and query nothing
        results = fetcher.fetch_all("test", sources=["not_a_real_source"])
        assert results == []
