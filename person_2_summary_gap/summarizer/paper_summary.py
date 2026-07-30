"""
person_2_summary_gap/summarizer/paper_summary.py

Builds the prompt for a single paper and parses the LLM's JSON response
into a PaperSummary object. Kept separate from summary_agent.py so the
prompt-building/parsing logic can be unit tested without hitting the API.
"""

from __future__ import annotations

from pathlib import Path

from shared.schemas.paper_schema import Paper
from shared.schemas.summary_schema import PaperSummary
from shared.utils.helpers import extract_json
from shared.utils.logger import get_logger

logger = get_logger(__name__)

_PROMPT_PATH = Path(__file__).resolve().parents[2] / "shared" / "prompts" / "summary_prompt.txt"


def _load_prompt_template() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


def build_summary_prompt(paper: Paper) -> str:
    """Fill the summary prompt template for a single paper."""
    template = _load_prompt_template()
    return template.format(
        title=paper.title,
        paper_text=paper.text_for_llm(),
    )


def parse_summary_response(paper: Paper, raw_response: str) -> PaperSummary:
    """Parse the model's raw text response into a PaperSummary."""
    try:
        data = extract_json(raw_response)
    except ValueError as exc:
        logger.warning("Failed to parse summary JSON for %s: %s", paper.id, exc)
        return PaperSummary(
            paper_id=paper.id,
            title=paper.title,
            tldr="Summary unavailable (parse error).",
        )

    return PaperSummary(
        paper_id=paper.id,
        title=paper.title,
        problem=data.get("problem", ""),
        method=data.get("method", ""),
        findings=data.get("findings", ""),
        contributions=list(data.get("contributions", []) or []),
        keywords=list(data.get("keywords", []) or []),
        tldr=data.get("tldr", ""),
    )
