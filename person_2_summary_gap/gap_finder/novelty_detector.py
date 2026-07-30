"""
person_2_summary_gap/gap_finder/novelty_detector.py

Extracts the novel/distinguishing aspects of a single paper, using its
PaperSummary (from Person 2's own summarizer) as grounding context so we
don't need to re-read the full paper text.
"""

from __future__ import annotations

import anthropic

from shared.schemas.summary_schema import PaperSummary
from shared.schemas.gap_schema import PaperNovelty
from shared.utils.config import settings
from shared.utils.helpers import extract_json, retry
from shared.utils.logger import get_logger

logger = get_logger(__name__)

_NOVELTY_PROMPT = """Given this paper summary:

Title: {title}
Problem: {problem}
Method: {method}
Findings: {findings}
Contributions: {contributions}

List the specific aspects of this paper that are novel or distinguish it from
typical prior work in the area. Respond with ONLY a JSON object:

{{"novel_aspects": ["aspect 1", "aspect 2"]}}

If nothing stands out as clearly novel, return an empty list."""


class NoveltyDetector:
    def __init__(self, client: anthropic.Anthropic | None = None):
        self.client = client or anthropic.Anthropic(api_key=settings.anthropic_api_key)

    @retry(times=2, delay_seconds=1.0)
    def _call_model(self, prompt: str) -> str:
        response = self.client.messages.create(
            model=settings.model_name,
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        parts = [b.text for b in response.content if getattr(b, "type", "") == "text"]
        return "\n".join(parts)

    def detect(self, summary: PaperSummary) -> PaperNovelty:
        prompt = _NOVELTY_PROMPT.format(
            title=summary.title,
            problem=summary.problem,
            method=summary.method,
            findings=summary.findings,
            contributions="; ".join(summary.contributions),
        )
        try:
            raw = self._call_model(prompt)
            data = extract_json(raw)
            novel_aspects = list(data.get("novel_aspects", []) or [])
        except Exception as exc:  # noqa: BLE001
            logger.warning("Novelty detection failed for %s: %s", summary.paper_id, exc)
            novel_aspects = []
        return PaperNovelty(paper_id=summary.paper_id, novel_aspects=novel_aspects)
