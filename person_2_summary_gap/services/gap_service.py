"""
person_2_summary_gap/services/gap_service.py

Thin service layer between main.py (FastAPI routes) and GapAgent.
Takes PaperSummary objects (produced by SummaryService) as input, since
gap-finding builds on top of the summarization step.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from shared.schemas.summary_schema import PaperSummary
from shared.schemas.gap_schema import GapAnalysis
from shared.utils.config import settings
from shared.utils.logger import get_logger

from ..gap_finder.gap_agent import GapAgent

logger = get_logger(__name__)


class GapService:
    def __init__(self, agent: GapAgent | None = None):
        self.agent = agent or GapAgent()

    def run(self, summaries: List[PaperSummary], save: bool = True) -> GapAnalysis:
        if not summaries:
            return GapAnalysis(
                num_papers_analyzed=0,
                errors=["No paper summaries provided to analyze for gaps."],
            )

        analysis = self.agent.run(summaries)

        if save:
            self._save(analysis)

        return analysis

    def _save(self, analysis: GapAnalysis) -> None:
        out_dir = Path(settings.outputs_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "gaps.json"
        out_path.write_text(
            json.dumps(json.loads(analysis.model_dump_json()), indent=2),
            encoding="utf-8",
        )
        logger.info("Saved gap analysis output to %s", out_path)
