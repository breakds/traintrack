import os
from typing import List
from contextlib import contextmanager
import asyncio
from collections import deque

import paramiko
from loguru import logger

from traintrack.schema.central_config import CentralConfig, EndPointConfig
from traintrack.schema.job import JobDescription, RunJobResponse
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


# TODO(breakds): There is a lot of IO. We should support await for them.
class CentralScheduler(object):
    def __init__(self):
        config_file_path = os.environ.get("TRAINTRACK_CENTRAL_CONFIG")
        if config_file_path is None:
            raise ValueError(
                "TRAINTRACK_CENTRAL_CONFIG environment variable is not set"
            )
        self._config = CentralConfig.parse_file(config_file_path)
        self._queue = deque()
        self._event_loop = asyncio.new_event_loop()

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
            return "".join(result)

    def fetch_post(self, end_point: EndPointConfig, api: str, payload: str) -> str | None:
        with ssh_client(end_point) as ssh:
            if ssh is None:
                return None

            stdin, stdout, stderr = ssh.exec_command(
                'curl -X POST -H "Content-Type: application/json" '
                f"-d '{payload}' "
                f"http://localhost:{end_point.port}/{api}"
            )

            result = []
            for line in stdout.readlines():
                result.append(line)
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

    def _try_schedule(self):
        """Query all the agents and schedule jobs if possible.

        Note that this function can only be called within scheduler's event loop
        in order to be thread safe.

        """
        scheduled = 0
        for agent in self._config.agents:
            if len(self._queue) == 0:
                break
            response = self.fetch_get(agent, "status")
            if response is None:
                logger.warning(f"Agent {agent.name} is unreachable.")
                continue
            agent_status = AgentStatus.parse_raw(response)
            count = 0
            for w in agent_status.workers:
                if w.available:
                    count += 1
            logger.info(f"Agent {agent.name} has {count} / {len(agent_status.workers)} "
                        "available.")
            while count > 0 and len(self._queue) > 0:
                job = self._queue.pop()
                response = self.fetch_post(agent, "run", payload=job.json())
                if response is None:
                    logger.warning(f"Agent {agent.name} is unreachable.")
                    break
                response = RunJobResponse.parse_raw(response)
                if not response.accepted:
                    logger.warning(f"Agent {agent.name} refuse to run job "
                                   f"{job.group}.{job.name}. Reason: {response.reason}")
                    break
                logger.success(f"Job {job.group}.{job.name} scheduled to "
                               f"run on {agent.name}.")
                scheduled += 1
                count = count - 1
            if scheduled > 0:
                logger.success(f"Successfully scheduled {scheduled} jobs.")

    def enqueue(self, job: JobDescription) -> bool:
        async def _enqueue():
            self._queue.appendleft(job)
            self._try_schedule()
        self._event_loop.run_until_complete(_enqueue())
        return True

    def try_schedule(self):
        self._event_loop.call_soon_threadsafe(self._try_schedule)

    def list_jobs(self) -> List[JobDescription]:
        result = []
        async def _list_jobs():
            for i in range(len(self._queue)):
                result.append(self._queue[i])
        self._event_loop.run_until_complete(_list_jobs())
        return result
