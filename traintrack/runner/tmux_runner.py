import socket
import subprocess
import libtmux
from loguru import logger

from traintrack.schema.agent_config import AgentConfig
from traintrack.schema.job import JobDescription, RunJobResponse
from traintrack.schema.status import WorkerStatus


class TmuxRunner(object):
    def __init__(self, agent_config: AgentConfig):
        try:
            subprocess.run(["tmux", "start-server"], check=True)
        except subprocess.CalledProcessError as e:
            logger.critical("Cannot ensure tmux server running. Abort.")
            raise e

        self._worker_config = agent_config.workers
        self._server = libtmux.Server()
        for i in range(len(self._worker_config)):
            self.ensure_window(i)

    def ensure_session(self) -> libtmux.Session:
        for s in self._server.sessions:
            if s.name == "traintrack_agent":
                logger.info("Tmux session 'traintrack_agent' exists.")
                return s

        logger.info("Tmux session 'traintrack_agent' does not exist. Creating one.")
        s = self._server.new_session(
            session_name="traintrack_agent")
        logger.info("Tmux session 'traintrack_agent' created.")
        return s

    def ensure_window(self, worker_id: int) -> libtmux.Window:
        session = self.ensure_session()
        worker_name = f"worker{worker_id}"
        for w in session.windows:
            if w.name == worker_name:
                return w

        logger.info(f"Tmux worker '{worker_name}' does not exist. Creating one.")
        w = session.new_window(window_name=worker_name, attach=False)
        logger.info(f"Tmux worker '{worker_name}' created.")
        return w

    @property
    def num_workers(self):
        return len(self._worker_config)

    def is_worker_available(self, w: libtmux.Window) -> bool:
        # TODO(breakds): Need a more sophisticated way to check availability.
        # The current approach is simplified and prone to race condition.
        return w.panes[0].pane_current_command == "zsh"

    def run_job(self, job: JobDescription) -> RunJobResponse:
        # First select a worker
        pane = None
        worker_id = -1
        for i in range(self.num_workers):
            w = self.ensure_window(i)
            if self.is_worker_available(w):
                pane = w.panes[0]
                worker_id = i
                break
        if pane is None:
            logger.info("No available worker.")
            return RunJobResponse(
                accepted=False,
                reason="No available worker.")

        logger.info(f"Found available worker {worker_id}")
        # TODO(breakds): cd to the directory and handle repo
        pane.send_keys(job.command, enter=True)
        return RunJobResponse(
            accepted=True)

    def status(self):
        host = socket.gethostname()
        info = []
        for i in range(self.num_workers):
            w = self.ensure_window(i)
            info.append(WorkerStatus(
                host=host,
                id=i,
                available=self.is_worker_available(w)))
        return info
