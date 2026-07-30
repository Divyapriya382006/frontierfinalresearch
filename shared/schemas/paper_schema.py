"""
shared/schemas/paper_schema.py

Canonical representation of a research paper as it flows between
Person 1 (literature ranking) -> Person 2 (summary + gap finding)
-> Person 3 (dataset + planner) -> Person 4 (orchestrator + frontend).
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class Paper(BaseModel):
    """A single paper as produced by Person 1's fetch/ranking pipeline."""

    id: str = Field(default="", description="Stable id, e.g. arXiv id or DOI or a hash")
    title: str
    authors: List[str] = Field(default_factory=list)
    abstract: str = ""
    full_text: Optional[str] = Field(
        default=None,
        description="Full paper text if available. Falls back to abstract if missing.",
    )
    year: Optional[int] = None
    venue: Optional[str] = None
    url: Optional[str] = None
    pdf_url: Optional[str] = None
    doi: Optional[str] = None
    source: Optional[str] = Field(default=None, description="e.g. 'semantic_scholar', 'arxiv', 'openalex'")
    source_id: str = ""
    citation_count: Optional[int] = None
    fields_of_study: List[str] = Field(default_factory=list)
    relevance_score: Optional[float] = Field(default=None, description="Score assigned by Person 1's ranking module")
    citation_score: Optional[float] = None
    recency_score: Optional[float] = None
    final_score: Optional[float] = None
    venue_quality_score: Optional[float] = None

    def text_for_llm(self, max_chars: int = 6000) -> str:
        """Best-available text to feed an LLM: full text if present, else abstract."""
        text = self.full_text or self.abstract or ""
        return text[:max_chars]

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> "Paper":
        return cls(**data)

    def dedup_key(self) -> str:
        """A loose key used as a first-pass exact-match dedup signal."""
        if self.doi:
            return f"doi:{self.doi.lower().strip()}"
        return f"title:{self.title.lower().strip()}"


class PaperList(BaseModel):
    papers: List[Paper] = Field(default_factory=list)
