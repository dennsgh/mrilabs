from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Task(BaseModel):
    task: str
    description: Optional[str] = None
    delay: float = 0.0  # Ensuring delay is always treated as a float
    parameters: Dict[str, Any] = Field(
        default_factory=dict
    )  # Using default_factory for parameters


class Experiment(BaseModel):
    name: Optional[str] = None
    steps: List[Task]


class ExperimentWrapper(BaseModel):
    experiment: Experiment
