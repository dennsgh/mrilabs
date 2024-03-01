from typing import Any, Dict, List

from pydantic import BaseModel


# At the moment these are unused.
class Task(BaseModel):
    task: str
    description: str
    duration: int
    parameters: Dict[str, Any]


class Experiment(BaseModel):
    name: str
    steps: List[Task]


class TaskDictionary(BaseModel):
    task: str
    description: str
    duration: int
    parameters: Dict[str, Any]
