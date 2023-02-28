import os
import socket
import asyncio
from typing import List

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from traintrack.scheduler import CentralScheduler
from traintrack.schema.job import JobDescription, JobRequest
from traintrack.schema.status import ListWorkersResponse


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


scheduler = CentralScheduler()


@app.on_event("startup")
def on_startup():
    async def _periodic_try_schedule():
        global scheduler
        while True:
            scheduler._try_schedule()
            await asyncio.sleep(scheduler._config.schedule_interval)

    asyncio.create_task(_periodic_try_schedule())
    logger.success(f"Traintrack central started on {socket.gethostname()}.")


@app.get("/workers")
def list_workers() -> ListWorkersResponse:
    global scheduler
    return ListWorkersResponse(workers=scheduler.list_workers())


@app.post("/enqueue")
def enqueue_job(job: JobRequest):
    global scheduler
    success = scheduler.enqueue(job)
    return {"success": success}


@app.get("/jobs")
def list_jobs() -> List[JobRequest]:
    global scheduler
    return scheduler.list_jobs()


@app.get("/disable/{agent_name}")
def disable_agent(agent_name: str):
    global scheduler
    scheduler.disable_agent(agent_name)
    return scheduler.agent_blacklist


@app.get("/enable/{agent_name}")
def enable_agent(agent_name: str):
    global scheduler
    scheduler.enable_agent(agent_name)
    return scheduler.agent_blacklist


@app.get("/blacklist")
def agent_blacklist():
    global scheduler
    return scheduler.agent_blacklist


def main():
    port = os.environ.get("TRAINTRACK_CENTRAL_PORT")
    if port is None:
        port = 5976
    else:
        port = int(port)
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")


if __name__ == "__main__":
    main()
