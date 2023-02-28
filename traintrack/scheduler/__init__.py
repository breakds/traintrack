import os
from typing import List
from contextlib import contextmanager
from collections import deque
import threading

import paramiko
from loguru import logger

from traintrack.schema.central_config import CentralConfig, EndPointConfig
from traintrack.schema.job import JobRequest, RunJobResponse
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
        self._lock = threading.Lock()

        self._agent_blacklist = set(self._config.default_blacklist)

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

    def fetch_post(
        self, end_point: EndPointConfig, api: str, payload: str
    ) -> str | None:
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
            if agent.name in self._agent_blacklist:
                # TODO(breakds): This is just a temporary solution.
                workers.append(
                    WorkerStatus(
                        host=agent.name, id=-1, gpu_type="N/A", available=False
                    )
                )
                continue
            response = self.fetch_get(agent, "status")
            if response is None:
                logger.warning(f"Agent {agent.name} is unreachable.")
                continue
            agent_status = AgentStatus.parse_raw(response)
            workers += agent_status.workers

        return workers

    def find_agent_by_name(self, name: str):
        for agent in self._config.agents:
            if agent.name == name:
                return agent
        raise KeyError(f"Cannot find agent with name '{name}'.")

    def _try_schedule(self):
        """Query all the agents and schedule jobs if possible.

        Note that this function can only be called within scheduler's event loop
        in order to be thread safe.

        """
        # First scan all the agents and get the number of available workers on
        # each agent.
        worker_count = {}
        for agent in self._config.agents:
            if agent.name in self._agent_blacklist:
                continue
            response = self.fetch_get(agent, "status")
            if response is None:
                logger.warning(f"Agent {agent.name} is unreachable.")
                continue
            count = 0
            agent_status = AgentStatus.parse_raw(response)
            for w in agent_status.workers:
                if w.available:
                    count += 1
            worker_count[agent.name] = count

        with self._lock:
            scheduled = []
            unscheduled = []
            while len(self._queue) > 0:
                job_req: JobRequest = self._queue.pop()  # Pop from right
                logger.info(f"Scheduling {job_req} ...")
                success = False
                for agent_name, count in worker_count:
                    if agent_name in job_req.agent_blacklist or count == 0:
                        continue

                    agent = self.find_agent_by_name(agent_name)
                    response = self.fetch_post(agent, "run", payload=job_req.job.json())
                    if response is None:
                        logger.warning(f"Agent {agent.name} is unreachable.")
                        worker_count[agent_name] = 0
                        continue

                    job_name = f"{job_req.job.group}.{job_req.job.name}"
                    response = RunJobResponse.parse_raw(response)
                    if not response.accepted:
                        logger.warning(
                            f"Agent {agent_name} refuse to run job "
                            f"{job_name} - reason: {response.reason}"
                        )
                        continue
                    logger.success(f"Job {job_name} scheduled to run on {agent_name}.")
                    success = True
                    break

                if success:
                    scheduled.append(job_req)
                else:
                    unscheduled.append(job_req)

            for job_req in unscheduled:
                self._queue.appendleft(job_req)  # Append from right

    def enqueue(self, job: JobRequest) -> bool:
        with self._lock:
            self._queue.appendleft(job)
        self._try_schedule()
        return True

    def list_jobs(self) -> List[JobRequest]:
        with self._lock:
            result = []
            for i in range(len(self._queue)):
                result.append(self._queue[i])
            return result

    def disable_agent(self, agent_name: str):
        self._agent_blacklist.add(agent_name)

    def enable_agent(self, agent_name: str):
        if agent_name in self._agent_blacklist:
            self._agent_blacklist.remove(agent_name)

    @property
    def agent_blacklist(self) -> List[str]:
        return list(self._agent_blacklist)
