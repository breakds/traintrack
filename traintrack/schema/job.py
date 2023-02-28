from typing import Dict, List
from pydantic import BaseModel


class HobotSpec(BaseModel):
    branch: str
    config: str
    overrides: Dict[str, str] = {}


class JobDescription(BaseModel):
    # wandb identifiers
    project: str
    group: str
    name: str
    notes: str | None = None

    # Task specification
    repo: str
    spec: HobotSpec


class JobRequest(BaseModel):
    job: JobDescription
    # Do not use agents from this list for this job
    agent_blacklist: List[str] = []


class JobList(BaseModel):
    jobs: List[JobDescription]


# TODO(breakds): Add datetime in the response
class RunJobResponse(BaseModel):
    accepted: bool
    reason: str | None = None
