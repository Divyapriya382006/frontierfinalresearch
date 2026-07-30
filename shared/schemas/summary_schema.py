"""
shared/schemas/summary_schema.py

Output contract for Person 2's summarizer module.
Person 4's orchestrator/proposal builder consumes these shapes directly,
so keep field names stable.
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class PaperSummary(BaseModel):
    """Per-paper structured summary."""

    paper_id: str
    title: str
    problem: str = Field(default="", description="What problem the paper addresses")
    method: str = Field(default="", description="What approach/method was used")
    findings: str = Field(default="", description="Key results / findings")
    contributions: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    tldr: str = Field(default="", description="One or two sentence summary")


class OverallSummary(BaseModel):
    """Aggregate summary across a whole set of papers."""

    num_papers: int
    common_themes: List[str] = Field(default_factory=list)
    methodologies_used: List[str] = Field(default_factory=list)
    key_trends: str = ""
    synthesis: str = Field(
        default="", description="A short narrative tying the papers together"
    )
    paper_summaries: List[PaperSummary] = Field(default_factory=list)


class SummaryResponse(BaseModel):
    """Top-level response returned by the /summarize API endpoint."""

    overall_summary: OverallSummary
    errors: List[str] = Field(default_factory=list)
