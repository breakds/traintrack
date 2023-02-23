from typing import List
from pydantic import BaseModel


class WorkerConfig(BaseModel):
    gpu_id: int
    gpu_type: str


class AgentConfig(BaseModel):
    workers: List[WorkerConfig]
