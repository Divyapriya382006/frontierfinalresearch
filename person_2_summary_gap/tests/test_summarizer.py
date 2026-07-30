"""
Tests for person_2_summary_gap/summarizer.

These tests mock the Anthropic client entirely, so they run offline
and without an API key.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from shared.schemas.paper_schema import Paper
from shared.schemas.summary_schema import PaperSummary
from person_2_summary_gap.summarizer.paper_summary import (
    build_summary_prompt,
    parse_summary_response,
)
from person_2_summary_gap.summarizer.overall_summary import build_overall_summary
from person_2_summary_gap.summarizer.summary_agent import SummaryAgent


def make_paper(paper_id="p1", title="Test Paper", abstract="This paper studies X.") -> Paper:
    return Paper(id=paper_id, title=title, authors=["A. Author"], abstract=abstract)


def mock_text_response(payload: dict):
    """Build a fake anthropic Message response object."""
    block = SimpleNamespace(type="text", text=json.dumps(payload))
    return SimpleNamespace(content=[block])


def test_build_summary_prompt_includes_title_and_text():
    paper = make_paper()
    prompt = build_summary_prompt(paper)
    assert "Test Paper" in prompt
    assert "This paper studies X." in prompt


def test_parse_summary_response_happy_path():
    paper = make_paper()
    raw = json.dumps(
        {
            "problem": "Problem X",
            "method": "Method Y",
            "findings": "Findings Z",
            "contributions": ["contribution 1"],
            "keywords": ["kw1", "kw2"],
            "tldr": "A short summary.",
        }
    )
    summary = parse_summary_response(paper, raw)
    assert isinstance(summary, PaperSummary)
    assert summary.paper_id == "p1"
    assert summary.problem == "Problem X"
    assert summary.keywords == ["kw1", "kw2"]


def test_parse_summary_response_handles_malformed_json():
    paper = make_paper()
    summary = parse_summary_response(paper, "not valid json at all")
    assert summary.paper_id == "p1"
    assert "unavailable" in summary.tldr.lower()


def test_build_overall_summary_aggregates_keywords():
    summaries = [
        PaperSummary(paper_id="p1", title="P1", keywords=["nlp", "transformers"], method="Method A"),
        PaperSummary(paper_id="p2", title="P2", keywords=["nlp", "graphs"], method="Method B"),
    ]
    overall = build_overall_summary(summaries, synthesis="A synthesis.")
    assert overall.num_papers == 2
    assert "nlp" in overall.common_themes
    assert overall.synthesis == "A synthesis."
    assert len(overall.paper_summaries) == 2


def test_summary_agent_summarize_paper_uses_mocked_client():
    fake_client = MagicMock()
    fake_client.messages.create.return_value = mock_text_response(
        {
            "problem": "P",
            "method": "M",
            "findings": "F",
            "contributions": ["c1"],
            "keywords": ["k1"],
            "tldr": "TLDR here.",
        }
    )
    agent = SummaryAgent(client=fake_client)
    paper = make_paper()

    summary = agent.summarize_paper(paper)

    assert summary.tldr == "TLDR here."
    assert fake_client.messages.create.called


def test_summary_agent_run_produces_overall_summary():
    fake_client = MagicMock()
    fake_client.messages.create.side_effect = [
        mock_text_response(
            {
                "problem": "P1",
                "method": "M1",
                "findings": "F1",
                "contributions": [],
                "keywords": ["k1"],
                "tldr": "TLDR 1",
            }
        ),
        # synthesis call returns plain text, not JSON
        SimpleNamespace(content=[SimpleNamespace(type="text", text="A synthesis paragraph.")]),
    ]
    agent = SummaryAgent(client=fake_client)
    papers = [make_paper("p1")]

    overall = agent.run(papers)

    assert overall.num_papers == 1
    assert overall.synthesis == "A synthesis paragraph."
