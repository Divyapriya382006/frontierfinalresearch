"""
Person 3 - Dataset Recommendation & Experiment Planner service.

Exposes a single endpoint per the shared API contract:
    POST /planner  ->  { datasets: DatasetRecommendation, experiment: ExperimentPlan }

Run standalone:
    uvicorn person_3_dataset_planner.main:app --reload --port 8003

Run a quick smoke test without the API layer:
    python -m person_3_dataset_planner.main
"""
import logging
import sys
from pathlib import Path
from typing import Optional

# Allow running this file directly (adds repo root to sys.path).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI
from pydantic import BaseModel

from person_3_dataset_planner.services.dataset_service import run_dataset_pipeline, load_context_from_person2
from person_3_dataset_planner.services.planner_service import run_planner_pipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("research_agent_x.person3.main")

app = FastAPI(title="ResearchAgentX - Person 3: Dataset & Planner Service")


class PlannerRequest(BaseModel):
    topic: str
    summary: Optional[str] = ""   # Person 2's overall_summary text, if available
    gaps: Optional[str] = ""      # Person 2's gaps text, if available
    total_weeks: Optional[float] = 8.0


@app.get("/health")
def health():
    return {"status": "ok", "service": "person_3_dataset_planner"}


@app.post("/planner")
def planner(request: PlannerRequest):
    """
    Single entrypoint matching the shared API contract:
    runs dataset recommendation, then feeds the result into experiment
    planning, and returns both (also written to outputs/*.json).
    """
    dataset_recommendation = run_dataset_pipeline(
        topic=request.topic,
        summary=request.summary or "",
        gaps=request.gaps or "",
    )

    experiment_plan = run_planner_pipeline(
        topic=request.topic,
        selected_datasets=[d.model_dump() for d in dataset_recommendation.recommended_datasets],
        gaps=request.gaps or "",
        total_weeks=request.total_weeks or 8.0,
    )

    return {
        "datasets": dataset_recommendation.to_dict(),
        "experiment": experiment_plan.to_dict(),
    }


def _run_smoke_test():
    """Runs the full pipeline locally with the mock Person 2 outputs, no server needed."""
    topic = "Efficient fine-tuning of large language models for low-resource languages"
    summary, gaps = load_context_from_person2()

    recommendation = run_dataset_pipeline(topic=topic, summary=summary, gaps=gaps)
    print("\n=== Dataset Recommendation ===")
    print(recommendation.model_dump_json(indent=2))

    plan = run_planner_pipeline(
        topic=topic,
        selected_datasets=[d.model_dump() for d in recommendation.recommended_datasets],
        gaps=gaps,
    )
    print("\n=== Experiment Plan ===")
    print(plan.model_dump_json(indent=2))


if __name__ == "__main__":
    _run_smoke_test()
