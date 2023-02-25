import os
import socket
from typing import List
from pydantic import parse_obj_as

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import paramiko
from loguru import logger


from traintrack.schema.central_config import CentralConfig, EndPointConfig
from traintrack.schema.job import JobDescription
from traintrack.schema.status import WorkerStatus


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CentralScheduler(object):
    def __init__(self):
        config_file_path = os.environ.get("TRAINTRACK_CENTRAL_CONFIG")
        if config_file_path is None:
            raise ValueError(
                "TRAINTRACK_CENTRAL_CONFIG environment variable is not set"
            )
        self._config = CentralConfig.parse_file(config_file_path)

    def fetch_get(self, end_point: EndPointConfig, api: str) -> str | None:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            proxy_command = (
                "ssh -o StrictHostKeyChecking=no "
                f"{end_point.ssh_proxy} nc "
                f"{end_point.ssh_uri} {end_point.ssh_proxy_port}"
            )
            print(proxy_command)
            ssh.connect(
                hostname=end_point.ssh_uri,
                username=os.environ.get("USER"),
                key_filename=end_point.ssh_key_file,
                sock=paramiko.ProxyCommand(proxy_command),
            )
        except Exception as e:
            logger.warning(f"SSH connection failed: {e}")
            return None

        logger.success(f"Successfully connected to {end_point.name}")

        stdin, stdout, stderr = ssh.exec_command(
            f"curl http://localhost:{end_point.port}/{api}"
        )
        print(f"curl http://localhost:{end_point.port}/{api}")

        result = []
        for line in stdout.readlines():
            result.append(line)
        ssh.close()
        print(result)
        return "".join(result)

    def list_workers(self) -> List[WorkerStatus]:
        worker_status = []
        for agent in self._config.agents:
            response = self.fetch_get(agent, "status")
            if response is None:
                logger.warning(f"Agent {agent.name} is unreachable.")
            worker_status += parse_obj_as(List[WorkerStatus], response)
        return worker_status


scheduler = CentralScheduler()


@app.on_event("startup")
async def on_startup():
    logger.success(f"Traintrack central started on {socket.gethostname()}.")


@app.get("/workers")
async def list_workers():
    global scheduler
    scheduler.list_workers()


def main():
    port = os.environ.get("TRAINTRACK_CENTRAL_PORT")
    if port is None:
        port = 5976
    else:
        port = int(port)
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")


if __name__ == "__main__":
    main()
