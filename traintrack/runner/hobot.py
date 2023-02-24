import time

import libtmux
from jinja2 import Environment
from traintrack.schema.agent_config import RepoConfig

from traintrack.schema.job import HobotSpec, JobDescription


_RUN_COMMAND="""
ALF_USE_GIN=0 python -m alf.bin.train --store_snapshot=false --conf {{config}} --root_dir {{root_dir}} {{extra}}
"""

def run_hobot_job(pane: libtmux.Pane, repo: RepoConfig, job: JobDescription):
    pane.send_keys(f"cd {repo.path}", enter=True)
    # Wait for nix develop to finish
    while pane.pane_current_command != "zsh":
        time.sleep(1)
    pane.send_keys(f"git reset --hard HEAD", enter=True)
    pane.send_keys(f"git fetch --all", enter=True)
    pane.send_keys(f"git switch {job.spec.branch}", enter=True)
    env = Environment()
    template = env.from_string(_RUN_COMMAND)

    assert job.project is not None
    root_dir = f"{repo.work_dir}/{job.project}/{job.group}.{job.name}"

    # TODO(breakds): Should I just delete the root_dir to make sure it is clean?

    command = template.render(
        config=job.spec.config,
        root_dir=root_dir)

    pane.send_keys(command, enter=True)
