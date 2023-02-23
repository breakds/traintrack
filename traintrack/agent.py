import socket

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from traintrack.schema.agent_config import AgentConfig, WorkerConfig

from traintrack.schema.job import JobDescription, RunJobResponse
from traintrack.runner.tmux_runner import TmuxRunner


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


runner = TmuxRunner(AgentConfig(workers=[WorkerConfig(gpu_id=0, gpu_type="3080")]))


@app.on_event("startup")
async def on_startup():
    global runner
    logger.success(f"Traintrack agent started on {socket.gethostname()}.")


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/run")
async def run_job(job: JobDescription):
    global runner
    return runner.run_job(job)


@app.get("/status")
async def status():
    global runner
    return runner.status()
