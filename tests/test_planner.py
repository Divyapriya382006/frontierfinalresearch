import json

from person_3_dataset_planner.planner.timeline import build_default_timeline
from person_3_dataset_planner.planner.planner_agent import build_experiment_plan
from shared.schemas.experiment_schema import ExperimentPlan


def test_build_default_timeline_sums_to_total_weeks():
    timeline = build_default_timeline(10.0)
    total = sum(p.duration_weeks for p in timeline.phases)
    assert abs(total - 10.0) < 0.5  # rounding tolerance
    assert timeline.total_duration_weeks == 10.0


def test_build_default_timeline_has_all_phases():
    timeline = build_default_timeline(8.0)
    phase_names = [p.phase for p in timeline.phases]
    assert "Literature Review & Setup" in phase_names
    assert "Write-up & Submission" in phase_names


def test_build_experiment_plan_dry_run_returns_valid_schema():
    # No ANTHROPIC_API_KEY in the test env -> DRY_RUN path -> deterministic default plan.
    datasets = [{"name": "FLORES-200", "task": "machine-translation"}]
    plan = build_experiment_plan("low-resource languages", datasets, gaps="", total_weeks=6.0)

    assert isinstance(plan, ExperimentPlan)
    assert plan.methodology.overview
    assert len(plan.methodology.steps) > 0
    assert len(plan.evaluation.metrics) > 0
    assert plan.timeline.total_duration_weeks == 6.0
    # Make sure it's actually JSON-serializable (what the connector will consume).
    json.dumps(plan.to_dict())
