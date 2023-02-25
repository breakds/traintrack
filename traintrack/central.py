import os
import socket
from typing import List

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from traintrack.scheduler import CentralScheduler
from traintrack.schema.job import JobDescription

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
    logger.success(f"Traintrack central started on {socket.gethostname()}.")


@app.get("/workers")
def list_workers() -> ListWorkersResponse:
    global scheduler
    return ListWorkersResponse(workers=scheduler.list_workers())


@app.post("/enqueue")
def enqueue_job(job: JobDescription):
    global scheduler
    success = scheduler.enqueue(job)
    return {
        "success": success
    }


@app.get("/jobs")
def list_jobs():
    global scheduler
    return scheduler.list_jobs()


def main():
    port = os.environ.get("TRAINTRACK_CENTRAL_PORT")
    if port is None:
        port = 5976
    else:
        port = int(port)
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")


if __name__ == "__main__":
    main()
