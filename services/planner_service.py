"""
Orchestrates the experiment-planning pipeline and writes
outputs/experiment.json (the file the connector/Person 4 consumes).
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

from person_3_dataset_planner.planner.planner_agent import build_experiment_plan
from shared.schemas.experiment_schema import ExperimentPlan

logger = logging.getLogger("research_agent_x.planner_service")

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "outputs"


def run_planner_pipeline(
    topic: str,
    selected_datasets: List[Dict[str, Any]],
    gaps: str = "",
    total_weeks: float = 8.0,
    write_output: bool = True,
) -> ExperimentPlan:
    """
    Full pipeline: given the datasets already selected by the dataset
    agent, ask the planner agent to design methodology + evaluation +
    timeline, then write outputs/experiment.json.
    """
    logger.info("Building experiment plan for topic: %r", topic)
    plan = build_experiment_plan(topic, selected_datasets, gaps=gaps, total_weeks=total_weeks)

    if write_output:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = OUTPUT_DIR / "experiment.json"
        out_path.write_text(json.dumps(plan.to_dict(), indent=2), encoding="utf-8")
        logger.info("Wrote %s", out_path)

    return plan
