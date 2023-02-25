import os
import json
from typing import List

import click
from loguru import logger
from pydantic import BaseModel
import pydantic
import questionary
import requests
from rich.table import Table
from rich.console import Console
from traintrack.schema.job import JobDescription

from traintrack.schema.status import ListWorkersResponse
from traintrack.templates.hobot import prompt_for_locomotion_job


PORT = os.environ.get("TRAINTRACK_CENTRAL_PORT") or 5976


def fetch(command: str, payload: BaseModel | None = None):
    if payload is not None:
        response = requests.post(f"http://localhost:{PORT}/{command}",
                                 json=payload.dict())
    else:
        response = requests.get(f"http://localhost:{PORT}/{command}")

    if response.status_code == 200:
        return json.loads(response.content)
    else:
        logger.error("Error trying to connected to the central server.")
        return None


@click.group()
def cli():
    pass


@cli.command()
def new():
    template = questionary.select(
        "Choose a template:",
        choices=[
            {"name": "hobot.locomotion", "value": "hobot.locomotion"},
            {"name": "hobot.whole_body", "value": "hobot.whole_body"},
        ],
    ).unsafe_ask()

    job = None
    if template == "hobot.locomotion":
        job = prompt_for_locomotion_job()
    else:
        raise RuntimeError(f"I do not recognize the template '{template}")

    if job is None:
        return

    logger.success("Job constrcuted. Please see below.")
    logger.info(job)
    confirm = questionary.confirm("Do you want to proceed?", default=True).ask()
    if not confirm:
        return

    result = fetch("enqueue", payload=job)
    if result is None:
        return

    if result["success"]:
        logger.success("Successfully submitted job.")
    else:
        logger.error("Job was rejected.")

@cli.command()
def workers():
    result = fetch("workers")
    if result is None:
        return
    worker_list = ListWorkersResponse.parse_obj(result)

    blacklist = fetch("blacklist") or []

    table = Table(title="All Workers")
    table.add_column("Agent", justify="right", no_wrap=True)
    table.add_column("Worker", justify="left", style="magenta", no_wrap=True)
    table.add_column("GPU", justify="left", style="cornflower_blue", no_wrap=True)
    table.add_column("Status", justify="full", no_wrap=True)

    for w in worker_list.workers:
        status = "[red]Busy"
        if w.available:
            status = "[green]Free"
        agent = f"[yellow]{w.host}"
        if w.host in blacklist:
            agent = f"{w.host} (disabled)"
        table.add_row(agent, f"{w.id}", w.gpu_type, status)
    console = Console()
    console.print(table)


@cli.command()
def jobs():
    result = fetch("jobs")
    if result is None:
        return
    job_list = pydantic.parse_obj_as(List[JobDescription], result)

    table = Table(title="All Jobs")
    table.add_column("Project", no_wrap=True)
    table.add_column("Group", no_wrap=True)
    table.add_column("Name", no_wrap=True)

    for j in job_list:
        table.add_row(j.project, j.group, j.name)
    console = Console()
    console.print(table)


@cli.command()
@click.argument("agent_name")
def enable(agent_name: str):
    fetch(f"enable/{agent_name}")


@cli.command()
@click.argument("agent_name")
def disable(agent_name: str):
    fetch(f"disable/{agent_name}")


if __name__ == "__main__":
    cli()
