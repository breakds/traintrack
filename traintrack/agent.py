import os
import socket

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from traintrack.schema.agent_config import AgentConfig

from traintrack.schema.job import JobDescription
from traintrack.runner.tmux_runner import TmuxRunner


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def init_runner() -> TmuxRunner:
    # Read the path to the configuration file from an environment variable
    config_file_path = os.environ.get("TRAINTRACK_AGENT_CONFIG")
    if config_file_path is None:
        raise ValueError("TRAINTRACK_AGENT_CONFIG environment variable is not set")

    # Load the agent configuration from the file
    with open(config_file_path, "r") as f:
        agent_config = AgentConfig.parse_raw(f.read())

    return TmuxRunner(agent_config)


runner = init_runner()


@app.on_event("startup")
async def on_startup():
    global runner
    logger.success(f"Traintrack agent started on {socket.gethostname()}.")


@app.get("/")
async def root():
    return {"status": "running"}


@app.post("/run")
async def run_job(job: JobDescription):
    global runner
    return runner.run_job(job)


@app.get("/status")
async def status():
    global runner
    return runner.status()


def main():
    port = os.environ.get("TRAINTRACK_AGENT_PORT")
    if port is None:
        port = 5975
    else:
        port = int(port)
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")    


if __name__ == "__main__":
    main()
