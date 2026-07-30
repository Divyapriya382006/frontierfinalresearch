"""
Tests for person_2_summary_gap/gap_finder.

Mocks the Anthropic client so tests run offline without an API key.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

from shared.schemas.summary_schema import PaperSummary
from person_2_summary_gap.gap_finder.novelty_detector import NoveltyDetector
from person_2_summary_gap.gap_finder.limitation_detector import LimitationDetector
from person_2_summary_gap.gap_finder.gap_agent import GapAgent


def mock_text_response(payload: dict):
    block = SimpleNamespace(type="text", text=json.dumps(payload))
    return SimpleNamespace(content=[block])


def make_summary(paper_id="p1") -> PaperSummary:
    return PaperSummary(
        paper_id=paper_id,
        title=f"Paper {paper_id}",
        problem="Some problem",
        method="Some method",
        findings="Some findings",
        contributions=["contribution 1"],
        keywords=["kw1"],
        tldr="TLDR",
    )


def test_novelty_detector_parses_response():
    fake_client = MagicMock()
    fake_client.messages.create.return_value = mock_text_response(
        {"novel_aspects": ["uses a new architecture"]}
    )
    detector = NoveltyDetector(client=fake_client)
    result = detector.detect(make_summary())
    assert result.paper_id == "p1"
    assert result.novel_aspects == ["uses a new architecture"]


def test_limitation_detector_parses_response():
    fake_client = MagicMock()
    fake_client.messages.create.return_value = mock_text_response(
        {"limitations": ["small dataset", "no baseline comparison"]}
    )
    detector = LimitationDetector(client=fake_client)
    result = detector.detect(make_summary())
    assert result.paper_id == "p1"
    assert len(result.limitations) == 2


def test_novelty_detector_handles_errors_gracefully():
    fake_client = MagicMock()
    fake_client.messages.create.side_effect = RuntimeError("API down")
    detector = NoveltyDetector(client=fake_client)
    result = detector.detect(make_summary())
    assert result.novel_aspects == []


def test_gap_agent_run_produces_gap_analysis():
    fake_client = MagicMock()
    fake_client.messages.create.side_effect = [
        # novelty detector call
        mock_text_response({"novel_aspects": ["novel thing"]}),
        # limitation detector call
        mock_text_response({"limitations": ["some limitation"]}),
        # gap synthesis call
        mock_text_response(
            {
                "gaps": [
                    {
                        "title": "Gap 1",
                        "description": "Description of gap 1",
                        "supporting_paper_ids": ["p1"],
                        "opportunity": "Do more research",
                        "confidence": 0.8,
                    }
                ]
            }
        ),
    ]
    agent = GapAgent(client=fake_client)
    summaries = [make_summary("p1")]

    analysis = agent.run(summaries)

    assert analysis.num_papers_analyzed == 1
    assert len(analysis.gaps) == 1
    assert analysis.gaps[0].title == "Gap 1"
    assert analysis.gaps[0].confidence == 0.8


def test_gap_agent_handles_malformed_gap_entries():
    fake_client = MagicMock()
    fake_client.messages.create.side_effect = [
        mock_text_response({"novel_aspects": []}),
        mock_text_response({"limitations": []}),
        mock_text_response({"gaps": [{"title": "Bad gap", "confidence": "not-a-float"}]}),
    ]
    agent = GapAgent(client=fake_client)
    summaries = [make_summary("p1")]

    analysis = agent.run(summaries)

    # malformed gap entry should be skipped rather than crash the pipeline
    assert analysis.gaps == []
