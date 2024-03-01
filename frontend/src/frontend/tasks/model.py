from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Task(BaseModel):
    task: str
    description: str
    delay: float = 0
    parameters: Dict[str, Any] = Field(
        default_factory=dict
    )  # Allows for dynamic parameters


class Experiment(BaseModel):
    name: str
    steps: List[Task]
