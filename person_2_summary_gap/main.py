"""
person_2_summary_gap/main.py

Standalone FastAPI service for Person 2's module. Can run independently
for local development/testing, or be mounted into Person 4's orchestrator.

Run with:
    uvicorn person_2_summary_gap.main:app --reload --port 8002
"""

from __future__ import annotations

from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from shared.schemas.paper_schema import Paper
from shared.schemas.summary_schema import SummaryResponse, PaperSummary
from shared.schemas.gap_schema import GapAnalysis
from shared.utils.logger import get_logger

from .services.summary_service import SummaryService
from .services.gap_service import GapService

logger = get_logger(__name__)

app = FastAPI(
    title="ResearchAgentX - Person 2: Summary & Gap Finder",
    description="Summarizes a set of papers and identifies research gaps across them.",
    version="1.0.0",
)

summary_service = SummaryService()
gap_service = GapService()


class SummarizeRequest(BaseModel):
    papers: List[Paper]


class FindGapsRequest(BaseModel):
    """Gap finding operates on already-produced paper summaries."""

    summaries: List[PaperSummary]


class PipelineRequest(BaseModel):
    """Convenience endpoint: papers in, both summary + gaps out."""

    papers: List[Paper]


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "person_2_summary_gap"}


@app.post("/summarize", response_model=SummaryResponse)
def summarize(request: SummarizeRequest) -> SummaryResponse:
    if not request.papers:
        raise HTTPException(status_code=400, detail="papers list cannot be empty")
    return summary_service.run(request.papers)


@app.post("/find-gaps", response_model=GapAnalysis)
def find_gaps(request: FindGapsRequest) -> GapAnalysis:
    if not request.summaries:
        raise HTTPException(status_code=400, detail="summaries list cannot be empty")
    return gap_service.run(request.summaries)


@app.post("/pipeline")
def pipeline(request: PipelineRequest) -> dict:
    """Run summarization then gap-finding in one call. This is the shape
    Person 4's orchestrator will most likely call."""
    if not request.papers:
        raise HTTPException(status_code=400, detail="papers list cannot be empty")

    summary_response = summary_service.run(request.papers)
    gap_analysis = gap_service.run(summary_response.overall_summary.paper_summaries)

    return {
        "summary": summary_response.model_dump(),
        "gaps": gap_analysis.model_dump(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("person_2_summary_gap.main:app", host="0.0.0.0", port=8002, reload=True)
