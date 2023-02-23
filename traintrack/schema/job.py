from typing import Dict
from pydantic import BaseModel


class JobDescription(BaseModel):
    # wandb identifiers
    group: str
    name: str
    notes: str | None = None

    # git settings
    repo: str
    commit: str

    # command
    command: str

    # hyper params
    override: Dict[str, str]


# TODO(breakds): Add datetime in the response
class RunJobResponse(BaseModel):
    accepted: bool
    reason: str | None = None
