from __future__ import annotations
from typing import List
from pydantic import BaseModel, Field

class TimelinePhase(BaseModel):
    phase: str
    duration_weeks: float
    deliverables: List[str] = Field(default_factory=list)

class Timeline(BaseModel):
    total_duration_weeks: float
    phases: List[TimelinePhase] = Field(default_factory=list)

class Methodology(BaseModel):
    overview: str
    steps: List[str] = Field(default_factory=list)
    baseline_models: List[str] = Field(default_factory=list)
    proposed_approach: str

class EvaluationMetric(BaseModel):
    name: str
    description: str

class EvaluationPlan(BaseModel):
    metrics: List[EvaluationMetric] = Field(default_factory=list)
    evaluation_protocol: str

class ExperimentPlan(BaseModel):
    topic: str
    methodology: Methodology
    evaluation: EvaluationPlan
    timeline: Timeline

    def to_dict(self) -> dict:
        return self.model_dump()
