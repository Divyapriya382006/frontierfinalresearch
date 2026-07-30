"""
Deterministic timeline scaffolding. Kept rule-based (not LLM) so the total
duration always sums exactly and demo output is reproducible.
"""
from shared.schemas.experiment_schema import Timeline, TimelinePhase

# Proportional split of a generic research project timeline.
_DEFAULT_PHASE_WEIGHTS = [
    ("Literature Review & Setup", 0.15, ["Finalize related work", "Set up environment & data pipeline"]),
    ("Dataset Preparation", 0.15, ["Clean and preprocess selected datasets", "Establish train/val/test splits"]),
    ("Baseline Implementation", 0.20, ["Reproduce baseline models", "Validate baseline metrics"]),
    ("Proposed Method Development", 0.30, ["Implement proposed approach", "Iterate on design based on val results"]),
    ("Evaluation & Analysis", 0.15, ["Run full evaluation suite", "Error analysis"]),
    ("Write-up & Submission", 0.05, ["Draft paper/report", "Finalize submission"]),
]


def build_default_timeline(total_weeks: float) -> Timeline:
    """Build a timeline with sensible default phase proportions for the given budget."""
    phases = [
        TimelinePhase(
            phase=name,
            duration_weeks=round(total_weeks * weight, 1),
            deliverables=deliverables,
        )
        for name, weight, deliverables in _DEFAULT_PHASE_WEIGHTS
    ]
    return Timeline(total_duration_weeks=total_weeks, phases=phases)
