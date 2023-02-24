from typing import Dict, List
from pydantic import BaseModel


class RepoConfig(BaseModel):
    path: str
    work_dir: str


class WorkerConfig(BaseModel):
    gpu_id: int
    gpu_type: str
    repos: Dict[str, RepoConfig]


class AgentConfig(BaseModel):
    workers: List[WorkerConfig]
