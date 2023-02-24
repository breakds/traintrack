from typing import List
from pydantic import BaseModel


class EndPointConfig(BaseModel):
    uri: str
    port: int


class CentralConfig(BaseModel):
    agents: List[EndPointConfig] = []
