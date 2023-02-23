from pydantic import BaseModel


class WorkerStatus(BaseModel):
    host: str
    id: int
    available: bool
