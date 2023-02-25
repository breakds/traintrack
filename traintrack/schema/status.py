from typing import List
from pydantic import BaseModel


class WorkerStatus(BaseModel):
    host: str
    id: int
    gpu_type: str
    available: bool


class AgentStatus(BaseModel):
    workers: List[WorkerStatus]


class ListWorkersResponse(BaseModel):
    workers: List[WorkerStatus]
