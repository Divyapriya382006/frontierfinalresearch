import json

from person_3_dataset_planner.dataset.recommender import rank_by_keyword_overlap
from person_3_dataset_planner.dataset.dataset_agent import recommend_datasets
from person_3_dataset_planner.dataset import benchmark_fetcher
from shared.schemas.dataset_schema import DatasetRecommendation


CANDIDATES = [
    {"name": "FLORES-200", "description": "Multilingual translation benchmark", "task": "machine-translation", "num_papers": 45, "url": ""},
    {"name": "MasakhaNER", "description": "NER for African languages", "task": "named-entity-recognition", "num_papers": 22, "url": ""},
    {"name": "ImageNet", "description": "Large scale image classification", "task": "image-classification", "num_papers": 9000, "url": ""},
]


def test_rank_by_keyword_overlap_prioritizes_relevant_candidates():
    ranked = rank_by_keyword_overlap("multilingual translation languages", CANDIDATES, top_k=2)
    names = [c["name"] for c in ranked]
    assert "FLORES-200" in names
    assert "ImageNet" not in names  # irrelevant candidate should be filtered out


def test_rank_by_keyword_overlap_respects_top_k():
    ranked = rank_by_keyword_overlap("languages", CANDIDATES, top_k=1)
    assert len(ranked) == 1


def test_benchmark_fetcher_falls_back_when_all_sources_unavailable(monkeypatch):
    # No KAGGLE/TAVILY keys set in test env, and Papers with Code mocked empty
    # -> every source returns [] -> fallback list kicks in.
    monkeypatch.setattr(
        "person_3_dataset_planner.dataset.paperswithcode.PapersWithCodeClient.search_datasets",
        lambda self, query, items_per_page=20: [],
    )
    results = benchmark_fetcher.fetch_candidate_datasets("some obscure topic")
    assert len(results) > 0  # fallback list kicks in
    assert all("name" in r and "source" in r for r in results)


def test_benchmark_fetcher_merges_and_tags_source(monkeypatch):
    monkeypatch.setattr(
        "person_3_dataset_planner.dataset.paperswithcode.PapersWithCodeClient.search_datasets",
        lambda self, query, items_per_page=20: [{"name": "PWC-Set", "url": "https://x.com/pwc", "task": "nlp"}],
    )
    monkeypatch.setattr(
        "person_3_dataset_planner.dataset.kaggle_client.KaggleClient.search_datasets",
        lambda self, query, max_results=20: [{"ref": "user/kaggle-set", "title": "Kaggle Set", "subtitle": "desc"}],
    )
    monkeypatch.setattr(
        "person_3_dataset_planner.dataset.tavily_client.TavilyClient.search_datasets",
        lambda self, query, max_results=10: [{"title": "Web Set", "url": "https://x.com/web", "content": "some dataset info"}],
    )
    results = benchmark_fetcher.fetch_candidate_datasets("topic")
    sources = {r["source"] for r in results}
    assert sources == {"paperswithcode", "kaggle", "tavily"}
    assert len(results) == 3


def test_recommend_datasets_dry_run_returns_valid_schema():
    # No ANTHROPIC_API_KEY in the test env -> DRY_RUN path -> heuristic fallback.
    recommendation = recommend_datasets("low-resource languages", CANDIDATES[:2])
    assert isinstance(recommendation, DatasetRecommendation)
    assert recommendation.topic == "low-resource languages"
    assert len(recommendation.recommended_datasets) > 0
    # Make sure it's actually JSON-serializable (what the connector will consume).
    json.dumps(recommendation.to_dict())


def test_recommend_datasets_handles_empty_candidates():
    recommendation = recommend_datasets("anything", [])
    assert recommendation.recommended_datasets == []


def test_load_context_from_person2_accepts_person2_payloads():
    from person_3_dataset_planner.services.dataset_service import load_context_from_person2

    summary_payload = {
        "overall_summary": {
            "num_papers": 1,
            "synthesis": "Parameter-efficient fine-tuning helps low-resource languages.",
            "paper_summaries": [{"title": "Example Paper", "tldr": "LoRA works well"}],
        },
        "errors": [],
    }
    gaps_payload = {
        "gaps": {
            "missing_eval": "No benchmark for truly low-resource languages",
        },
        "errors": [],
    }

    summary_text, gaps_text = load_context_from_person2(summary_payload=summary_payload, gaps_payload=gaps_payload)
    assert "low-resource" in summary_text.lower()
    assert "benchmark" in gaps_text.lower()
