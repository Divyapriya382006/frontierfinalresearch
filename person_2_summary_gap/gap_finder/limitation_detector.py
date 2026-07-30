"""
person_2_summary_gap/gap_finder/limitation_detector.py

Extracts stated or implied limitations of a single paper from its
PaperSummary.
"""

from __future__ import annotations

import anthropic

from shared.schemas.summary_schema import PaperSummary
from shared.schemas.gap_schema import PaperLimitation
from shared.utils.config import settings
from shared.utils.helpers import extract_json, retry
from shared.utils.logger import get_logger

logger = get_logger(__name__)

_LIMITATION_PROMPT = """Given this paper summary:

Title: {title}
Problem: {problem}
Method: {method}
Findings: {findings}

List the limitations of this paper's approach -- things it does not address,
scope restrictions, or weaknesses implied by the method/findings. Respond with
ONLY a JSON object:

{{"limitations": ["limitation 1", "limitation 2"]}}

If no limitations can be reasonably inferred, return an empty list."""


class LimitationDetector:
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

    def detect(self, summary: PaperSummary) -> PaperLimitation:
        prompt = _LIMITATION_PROMPT.format(
            title=summary.title,
            problem=summary.problem,
            method=summary.method,
            findings=summary.findings,
        )
        try:
            raw = self._call_model(prompt)
            data = extract_json(raw)
            limitations = list(data.get("limitations", []) or [])
        except Exception as exc:  # noqa: BLE001
            logger.warning("Limitation detection failed for %s: %s", summary.paper_id, exc)
            limitations = []
        return PaperLimitation(paper_id=summary.paper_id, limitations=limitations)
