"""
person_2_summary_gap/summarizer/summary_agent.py

SummaryAgent is the main entry point for Person 2's summarization work.
It:
  1. Summarizes each paper individually (paper_summary.py)
  2. Produces a short narrative synthesis across all papers
  3. Packages everything into an OverallSummary (overall_summary.py)

Uses the `anthropic` Python SDK. Requires ANTHROPIC_API_KEY to be set
(see shared/utils/config.py and .env.example).
"""

from __future__ import annotations

from typing import List

import anthropic

from shared.schemas.paper_schema import Paper
from shared.schemas.summary_schema import OverallSummary, PaperSummary
from shared.utils.config import settings
from shared.utils.helpers import retry
from shared.utils.logger import get_logger

from .paper_summary import build_summary_prompt, parse_summary_response
from .overall_summary import build_overall_summary

logger = get_logger(__name__)

_SYNTHESIS_PROMPT = """You are a research assistant. Below are one-sentence TL;DRs for {n} papers:

{tldrs}

Write a single short paragraph (3-5 sentences) synthesizing what this collection of papers,
taken together, is collectively trying to achieve and how the works relate to one another.
Respond with plain text only, no JSON, no markdown headers."""


class SummaryAgent:
    def __init__(self, client: anthropic.Anthropic | None = None):
        self.client = client or anthropic.Anthropic(api_key=settings.anthropic_api_key)

    @retry(times=3, delay_seconds=1.5)
    def _call_model(self, prompt: str, max_tokens: int | None = None) -> str:
        response = self.client.messages.create(
            model=settings.model_name,
            max_tokens=max_tokens or settings.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        parts = [block.text for block in response.content if getattr(block, "type", "") == "text"]
        return "\n".join(parts)

    def summarize_paper(self, paper: Paper) -> PaperSummary:
        """Summarize a single paper."""
        prompt = build_summary_prompt(paper)
        try:
            raw = self._call_model(prompt)
        except Exception as exc:  # noqa: BLE001
            logger.error("Model call failed for paper %s: %s", paper.id, exc)
            return PaperSummary(
                paper_id=paper.id,
                title=paper.title,
                tldr="Summary unavailable (API error).",
            )
        return parse_summary_response(paper, raw)

    def summarize_papers(self, papers: List[Paper]) -> List[PaperSummary]:
        """Summarize a list of papers, one at a time. Errors on one paper
        don't stop the rest -- they degrade to a placeholder summary."""
        summaries: List[PaperSummary] = []
        for paper in papers:
            logger.info("Summarizing paper: %s", paper.id)
            summaries.append(self.summarize_paper(paper))
        return summaries

    def synthesize(self, summaries: List[PaperSummary]) -> str:
        """Produce a short narrative paragraph tying all papers together."""
        if not summaries:
            return ""
        tldrs = "\n".join(f"- {s.tldr}" for s in summaries if s.tldr)
        if not tldrs:
            return ""
        prompt = _SYNTHESIS_PROMPT.format(n=len(summaries), tldrs=tldrs)
        try:
            return self._call_model(prompt, max_tokens=400).strip()
        except Exception as exc:  # noqa: BLE001
            logger.error("Synthesis call failed: %s", exc)
            return ""

    def run(self, papers: List[Paper]) -> OverallSummary:
        """Full pipeline: per-paper summaries -> synthesis -> OverallSummary."""
        summaries = self.summarize_papers(papers)
        synthesis = self.synthesize(summaries)
        return build_overall_summary(summaries, synthesis=synthesis)
