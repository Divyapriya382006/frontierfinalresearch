"""
shared/schemas/gap_schema.py

Output contract for Person 2's gap_finder module.
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class PaperLimitation(BaseModel):
    paper_id: str
    limitations: List[str] = Field(default_factory=list)


class PaperNovelty(BaseModel):
    paper_id: str
    novel_aspects: List[str] = Field(default_factory=list)


class ResearchGap(BaseModel):
    """A single identified gap in the literature."""

    title: str
    description: str
    supporting_paper_ids: List[str] = Field(default_factory=list)
    opportunity: str = Field(
        default="", description="Suggested direction to address this gap"
    )
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class GapAnalysis(BaseModel):
    """Top-level response returned by the /find-gaps API endpoint."""

    num_papers_analyzed: int
    limitations_by_paper: List[PaperLimitation] = Field(default_factory=list)
    novelty_by_paper: List[PaperNovelty] = Field(default_factory=list)
    gaps: List[ResearchGap] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
