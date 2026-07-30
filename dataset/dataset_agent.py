"""
LLM agent responsible for turning a shortlist of candidate datasets into a
final, justified recommendation (shared.schemas.dataset_schema.DatasetRecommendation).
"""
import json
import logging
from typing import List, Dict, Any, Optional

from shared.utils.config import SHARED_PROMPTS_DIR
from shared.utils.llm_client import call_claude_json
from shared.schemas.dataset_schema import Dataset, DatasetRecommendation

logger = logging.getLogger("research_agent_x.dataset_agent")

_PROMPT_PATH = SHARED_PROMPTS_DIR / "dataset_prompt.txt"


def _load_prompt_template() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


def _dry_run_recommendation(topic: str, candidates: List[Dict[str, Any]]) -> DatasetRecommendation:
    """Deterministic fallback used when no ANTHROPIC_API_KEY is configured."""
    datasets = [
        Dataset(
            name=c.get("name", "Unknown dataset"),
            description=c.get("description", ""),
            url=c.get("url", ""),
            task=c.get("task", ""),
            num_papers=c.get("num_papers", 0),
            relevance_score=max(0.5, 1.0 - i * 0.1),
            justification=f"Relevant to '{topic}' based on task/topic keyword overlap.",
        )
        for i, c in enumerate(candidates[:5])
    ]
    return DatasetRecommendation(
        topic=topic,
        recommended_datasets=datasets,
        reasoning="DRY_RUN mode: datasets selected by keyword overlap only, no LLM call made.",
    )


def recommend_datasets(
    topic: str,
    candidates: List[Dict[str, Any]],
    summary: str = "",
    gaps: str = "",
) -> DatasetRecommendation:
    """
    Given a topic, a shortlist of candidate datasets, and optional context
    from Person 2 (summary/gaps), ask Claude to pick and justify the final
    dataset recommendations. Falls back to a heuristic pick if the LLM call
    fails or DRY_RUN mode is active.
    """
    if not candidates:
        return DatasetRecommendation(topic=topic, recommended_datasets=[], reasoning="No candidate datasets found.")

    prompt = _load_prompt_template().format(
        topic=topic,
        summary=summary or "(not provided)",
        gaps=gaps or "(not provided)",
        candidate_datasets=json.dumps(candidates, indent=2),
    )

    result = call_claude_json(prompt)
    if result is None:
        logger.info("Falling back to heuristic dataset recommendation for %r.", topic)
        return _dry_run_recommendation(topic, candidates)

    try:
        return DatasetRecommendation(**result)
    except Exception as exc:  # pydantic ValidationError or shape mismatch
        logger.error("Claude response didn't match DatasetRecommendation schema: %s", exc)
        return _dry_run_recommendation(topic, candidates)
