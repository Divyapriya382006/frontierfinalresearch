"""
shared/schemas/paper_schema.py

<<<<<<< HEAD
Canonical Paper data model. Every source-specific fetcher (Semantic Scholar,
arXiv, OpenAlex) normalizes its raw API response into this shape, so the
rest of the pipeline (ranking, dedup, downstream agents 2-4) only ever has
to deal with one consistent structure.
=======
Canonical representation of a research paper as it flows between
Person 1 (literature ranking) -> Person 2 (summary + gap finding)
-> Person 3 (dataset + planner) -> Person 4 (orchestrator + frontend).

Everyone on the team should import `Paper` from here instead of
re-declaring their own paper dict shape.
>>>>>>> person2-integration
"""

from __future__ import annotations

<<<<<<< HEAD
from dataclasses import dataclass, field, asdict
from typing import List, Optional


@dataclass
class Paper:
    title: str
    abstract: str = ""
    authors: List[str] = field(default_factory=list)
=======
from typing import List, Optional
from pydantic import BaseModel, Field


class Paper(BaseModel):
    """A single paper as produced by Person 1's fetch/ranking pipeline."""

    id: str = Field(..., description="Stable id, e.g. arXiv id or DOI or a hash")
    title: str
    authors: List[str] = Field(default_factory=list)
    abstract: str = ""
    full_text: Optional[str] = Field(
        default=None,
        description="Full paper text if available. Falls back to abstract if missing.",
    )
>>>>>>> person2-integration
    year: Optional[int] = None
    venue: Optional[str] = None
    url: Optional[str] = None
    pdf_url: Optional[str] = None
<<<<<<< HEAD
    doi: Optional[str] = None
    source: str = ""
    source_id: str = ""
    citation_count: int = 0
    fields_of_study: List[str] = field(default_factory=list)

    # Populated later by the ranking stage
    relevance_score: float = 0.0
    citation_score: float = 0.0
    recency_score: float = 0.0
    final_score: float = 0.0
    venue_quality_score: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "Paper":
        known_fields = {f for f in Paper.__dataclass_fields__.keys()}
        filtered = {k: v for k, v in data.items() if k in known_fields}
        return Paper(**filtered)

    def dedup_key(self) -> str:
        """A loose key used as a first-pass exact-match dedup signal."""
        if self.doi:
            return f"doi:{self.doi.lower().strip()}"
        return f"title:{self.title.lower().strip()}"
=======
    citation_count: Optional[int] = None
    relevance_score: Optional[float] = Field(
        default=None, description="Score assigned by Person 1's ranking module"
    )
    source: Optional[str] = Field(
        default=None, description="e.g. 'semantic_scholar', 'arxiv', 'openalex'"
    )

    def text_for_llm(self, max_chars: int = 6000) -> str:
        """Best-available text to feed an LLM: full text if present, else abstract."""
        text = self.full_text or self.abstract or ""
        return text[:max_chars]


class PaperList(BaseModel):
    papers: List[Paper] = Field(default_factory=list)
>>>>>>> person2-integration
