from typing import List
from pydantic import BaseModel


class EndPointConfig(BaseModel):
    name: str
    port: int

    ssh_uri: str
    ssh_port: int
    ssh_proxy: str | None
    ssh_proxy_port: int | None
    ssh_key_file: str


class CentralConfig(BaseModel):
    agents: List[EndPointConfig] = []
    schedule_interval: int = 30
