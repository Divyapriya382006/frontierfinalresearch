"""
person_2_summary_gap/summarizer/overall_summary.py

Combines individual PaperSummary objects into one OverallSummary.
The "common themes" / "methodologies" extraction is done with lightweight
keyword aggregation locally (fast, free, deterministic); the narrative
synthesis paragraph is produced by the LLM via summary_agent.py.
"""

from __future__ import annotations

from collections import Counter
from typing import List

from shared.schemas.summary_schema import OverallSummary, PaperSummary


def _top_keywords(summaries: List[PaperSummary], top_n: int = 8) -> List[str]:
    counter: Counter[str] = Counter()
    for s in summaries:
        for kw in s.keywords:
            counter[kw.strip().lower()] += 1
    return [kw for kw, _ in counter.most_common(top_n)]


def _extract_methodologies(summaries: List[PaperSummary], top_n: int = 6) -> List[str]:
    methods = [s.method for s in summaries if s.method]
    # De-duplicate while preserving order, cap length for readability
    seen = []
    for m in methods:
        short = m.strip()
        if short and short not in seen:
            seen.append(short)
    return seen[:top_n]


def build_overall_summary(
    summaries: List[PaperSummary],
    synthesis: str = "",
) -> OverallSummary:
    """Combine per-paper summaries into a single OverallSummary object."""
    return OverallSummary(
        num_papers=len(summaries),
        common_themes=_top_keywords(summaries),
        methodologies_used=_extract_methodologies(summaries),
        key_trends=(
            f"{len(summaries)} papers analyzed; "
            f"{len(_top_keywords(summaries))} recurring themes identified."
        ),
        synthesis=synthesis,
        paper_summaries=summaries,
    )
