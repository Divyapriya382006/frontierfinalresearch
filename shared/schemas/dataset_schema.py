from __future__ import annotations
from typing import List
from pydantic import BaseModel, Field

class Dataset(BaseModel):
    name: str
    description: str
    url: str = ""
    task: str = ""
    num_papers: int = 0
    relevance_score: float = 0.0
    justification: str = ""

class DatasetRecommendation(BaseModel):
    topic: str
    recommended_datasets: List[Dataset] = Field(default_factory=list)
    reasoning: str = ""

    def to_dict(self) -> dict:
        return self.model_dump()
