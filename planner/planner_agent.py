"""
LLM agent responsible for producing the full ExperimentPlan: methodology,
evaluation plan, and timeline (shared.schemas.experiment_schema.ExperimentPlan).
"""
import json
import logging
from typing import List, Dict, Any

from shared.utils.config import SHARED_PROMPTS_DIR
from shared.utils.llm_client import call_claude_json
from shared.schemas.experiment_schema import ExperimentPlan, Timeline

from person_3_dataset_planner.planner.methodology import default_methodology
from person_3_dataset_planner.planner.evaluation import default_evaluation_plan
from person_3_dataset_planner.planner.timeline import build_default_timeline

logger = logging.getLogger("research_agent_x.planner_agent")

_PROMPT_PATH = SHARED_PROMPTS_DIR / "planner_prompt.txt"


def _load_prompt_template() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


def _dry_run_plan(topic: str, total_weeks: float) -> ExperimentPlan:
    return ExperimentPlan(
        topic=topic,
        methodology=default_methodology(topic),
        evaluation=default_evaluation_plan(topic),
        timeline=build_default_timeline(total_weeks),
    )


def build_experiment_plan(
    topic: str,
    selected_datasets: List[Dict[str, Any]],
    gaps: str = "",
    total_weeks: float = 8.0,
) -> ExperimentPlan:
    """
    Given a topic, the datasets Person 3's own dataset agent selected, and
    the research gaps from Person 2, ask Claude to design methodology +
    evaluation + timeline. Falls back to deterministic defaults if the LLM
    call fails or DRY_RUN mode is active, so downstream (Person 4's
    connector) always receives a valid ExperimentPlan.
    """
    prompt = _load_prompt_template().format(
        topic=topic,
        gaps=gaps or "(not provided)",
        selected_datasets=json.dumps(selected_datasets, indent=2),
        total_weeks=total_weeks,
    )

    result = call_claude_json(prompt)
    if result is None:
        logger.info("Falling back to default experiment plan for %r.", topic)
        return _dry_run_plan(topic, total_weeks)

    try:
        plan = ExperimentPlan(**result)
        # Guard against the LLM producing a timeline that doesn't sum
        # sensibly - if it's way off, fall back to the deterministic one.
        summed = sum(p.duration_weeks for p in plan.timeline.phases)
        if plan.timeline.phases and abs(summed - total_weeks) > total_weeks * 0.5:
            logger.warning("LLM timeline summed to %.1f weeks (expected ~%.1f); using default timeline.", summed, total_weeks)
            plan.timeline = build_default_timeline(total_weeks)
        return plan
    except Exception as exc:  # pydantic ValidationError or shape mismatch
        logger.error("Claude response didn't match ExperimentPlan schema: %s", exc)
        return _dry_run_plan(topic, total_weeks)
