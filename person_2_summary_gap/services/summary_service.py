"""
person_2_summary_gap/services/summary_service.py

Thin service layer between main.py (FastAPI routes) and SummaryAgent.
Handles saving outputs to disk so Person 4's orchestrator can pick them
up, and converts everything into the shared SummaryResponse contract.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from shared.schemas.paper_schema import Paper
from shared.schemas.summary_schema import SummaryResponse
from shared.utils.config import settings
from shared.utils.logger import get_logger

from ..summarizer.summary_agent import SummaryAgent

logger = get_logger(__name__)


class SummaryService:
    def __init__(self, agent: SummaryAgent | None = None):
        self.agent = agent or SummaryAgent()

    def run(self, papers: List[Paper], save: bool = True) -> SummaryResponse:
        errors: List[str] = []
        if not papers:
            errors.append("No papers provided to summarize.")

        overall_summary = self.agent.run(papers)
        response = SummaryResponse(overall_summary=overall_summary, errors=errors)

        if save:
            self._save(response)

        return response

    def _save(self, response: SummaryResponse) -> None:
        out_dir = Path(settings.outputs_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "summary.json"
        out_path.write_text(
            json.dumps(json.loads(response.model_dump_json()), indent=2),
            encoding="utf-8",
        )
        logger.info("Saved summary output to %s", out_path)
