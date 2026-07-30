"""
shared/schemas/paper_schema.py

Canonical Paper data model. Every source-specific fetcher (Semantic Scholar,
arXiv, OpenAlex) normalizes its raw API response into this shape, so the
rest of the pipeline (ranking, dedup, downstream agents 2-4) only ever has
to deal with one consistent structure.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import List, Optional


@dataclass
class Paper:
    title: str
    abstract: str = ""
    authors: List[str] = field(default_factory=list)
    year: Optional[int] = None
    venue: Optional[str] = None
    url: Optional[str] = None
    pdf_url: Optional[str] = None
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
