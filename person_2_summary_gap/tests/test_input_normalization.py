from __future__ import annotations

from shared.schemas.paper_schema import normalize_papers


def test_normalize_papers_accepts_person1_style_payload_with_top_level_list():
    payload = [
        {
            "title": "A paper from Person 1",
            "abstract": "This is a sample abstract.",
            "authors": ["Ada Lovelace"],
            "year": 2024,
            "venue": "Nature",
            "url": "https://example.com/paper",
            "citation_count": 42,
            "relevance_score": 0.91,
            "source": "openalex",
        }
    ]

    papers = normalize_papers(payload)

    assert len(papers) == 1
    assert papers[0].title == "A paper from Person 1"
    assert papers[0].abstract == "This is a sample abstract."
    assert papers[0].authors == ["Ada Lovelace"]
    assert papers[0].year == 2024
    assert papers[0].venue == "Nature"
    assert papers[0].source == "openalex"
    assert papers[0].id
