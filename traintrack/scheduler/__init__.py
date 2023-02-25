import os
from typing import List
from contextlib import contextmanager

import paramiko
from loguru import logger

from traintrack.schema.central_config import CentralConfig, EndPointConfig
from traintrack.schema.status import AgentStatus, WorkerStatus


@contextmanager
def ssh_client(end_point: EndPointConfig):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    try:
        proxy = None
        if end_point.ssh_proxy is not None:
            proxy = paramiko.ProxyCommand(
                "ssh -o StrictHostKeyChecking=no "
                f"{end_point.ssh_proxy} nc "
                f"{end_point.ssh_uri} {end_point.ssh_proxy_port}"
            )
        try:
            ssh.connect(
                hostname=end_point.ssh_uri,
                username=os.environ.get("USER"),
                key_filename=end_point.ssh_key_file,
                sock=proxy,
            )
        except Exception as e:
            logger.warning(f"SSH connection failed: {e}")
            ssh = None
        yield ssh
    finally:
        if ssh is not None:
            ssh.close()


class CentralScheduler(object):
    def __init__(self):
        config_file_path = os.environ.get("TRAINTRACK_CENTRAL_CONFIG")
        if config_file_path is None:
            raise ValueError(
                "TRAINTRACK_CENTRAL_CONFIG environment variable is not set"
            )
        self._config = CentralConfig.parse_file(config_file_path)

    def fetch_get(self, end_point: EndPointConfig, api: str) -> str | None:
        with ssh_client(end_point) as ssh:
            if ssh is None:
                return None

            stdin, stdout, stderr = ssh.exec_command(
                f"curl http://localhost:{end_point.port}/{api}"
            )

            result = []
            for line in stdout.readlines():
                result.append(line)
            ssh.close()
            return "".join(result)

    def list_workers(self) -> List[WorkerStatus]:
        workers = []
        for agent in self._config.agents:
            response = self.fetch_get(agent, "status")
            if response is None:
                logger.warning(f"Agent {agent.name} is unreachable.")
                continue
            agent_status = AgentStatus.parse_raw(response)
            workers += agent_status.workers

        return workers
