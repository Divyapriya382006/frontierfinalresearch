"""
person_2_summary_gap/gap_finder/gap_agent.py

GapAgent is the main entry point for Person 2's gap-finding work. It:
  1. Runs novelty_detector + limitation_detector over every paper summary
  2. Feeds the aggregated context to the LLM to synthesize cross-paper
     research gaps
  3. Packages everything into a GapAnalysis object
"""

from __future__ import annotations

from pathlib import Path
from typing import List

import anthropic

from shared.schemas.summary_schema import PaperSummary
from shared.schemas.gap_schema import (
    GapAnalysis,
    PaperLimitation,
    PaperNovelty,
    ResearchGap,
)
from shared.utils.config import settings
from shared.utils.helpers import extract_json, retry
from shared.utils.logger import get_logger

from .novelty_detector import NoveltyDetector
from .limitation_detector import LimitationDetector

logger = get_logger(__name__)

_PROMPT_PATH = Path(__file__).resolve().parents[2] / "shared" / "prompts" / "gap_prompt.txt"


def _load_gap_prompt_template() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


def _build_paper_context(
    summaries: List[PaperSummary],
    novelty: List[PaperNovelty],
    limitations: List[PaperLimitation],
) -> str:
    novelty_by_id = {n.paper_id: n.novel_aspects for n in novelty}
    limitations_by_id = {l.paper_id: l.limitations for l in limitations}

    blocks = []
    for s in summaries:
        blocks.append(
            "\n".join(
                [
                    f"Paper ID: {s.paper_id}",
                    f"Title: {s.title}",
                    f"Problem: {s.problem}",
                    f"Method: {s.method}",
                    f"Findings: {s.findings}",
                    f"Novel aspects: {', '.join(novelty_by_id.get(s.paper_id, [])) or 'none identified'}",
                    f"Limitations: {', '.join(limitations_by_id.get(s.paper_id, [])) or 'none identified'}",
                ]
            )
        )
    return "\n\n".join(blocks)


class GapAgent:
    def __init__(self, client: anthropic.Anthropic | None = None):
        self.client = client or anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.novelty_detector = NoveltyDetector(self.client)
        self.limitation_detector = LimitationDetector(self.client)

    @retry(times=3, delay_seconds=1.5)
    def _call_model(self, prompt: str) -> str:
        response = self.client.messages.create(
            model=settings.model_name,
            max_tokens=settings.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        parts = [b.text for b in response.content if getattr(b, "type", "") == "text"]
        return "\n".join(parts)

    def analyze_novelty_and_limitations(
        self, summaries: List[PaperSummary]
    ) -> tuple[List[PaperNovelty], List[PaperLimitation]]:
        novelty = [self.novelty_detector.detect(s) for s in summaries]
        limitations = [self.limitation_detector.detect(s) for s in summaries]
        return novelty, limitations

    def synthesize_gaps(
        self,
        summaries: List[PaperSummary],
        novelty: List[PaperNovelty],
        limitations: List[PaperLimitation],
    ) -> List[ResearchGap]:
        if not summaries:
            return []
        context = _build_paper_context(summaries, novelty, limitations)
        prompt = _load_gap_prompt_template().format(paper_context=context)
        try:
            raw = self._call_model(prompt)
            data = extract_json(raw)
            gaps_raw = data.get("gaps", []) or []
        except Exception as exc:  # noqa: BLE001
            logger.error("Gap synthesis failed: %s", exc)
            return []

        gaps: List[ResearchGap] = []
        for g in gaps_raw:
            try:
                gaps.append(
                    ResearchGap(
                        title=g.get("title", "Untitled gap"),
                        description=g.get("description", ""),
                        supporting_paper_ids=list(g.get("supporting_paper_ids", []) or []),
                        opportunity=g.get("opportunity", ""),
                        confidence=float(g.get("confidence", 0.5)),
                    )
                )
            except (TypeError, ValueError) as exc:
                logger.warning("Skipping malformed gap entry: %s (%s)", g, exc)
        return gaps

    def run(self, summaries: List[PaperSummary]) -> GapAnalysis:
        """Full pipeline: novelty + limitations per paper -> synthesized gaps."""
        novelty, limitations = self.analyze_novelty_and_limitations(summaries)
        gaps = self.synthesize_gaps(summaries, novelty, limitations)
        return GapAnalysis(
            num_papers_analyzed=len(summaries),
            limitations_by_paper=limitations,
            novelty_by_paper=novelty,
            gaps=gaps,
        )
