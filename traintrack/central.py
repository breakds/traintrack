import os
import socket

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


agents = []


@app.on_event("startup")
async def on_startup():
    global agents
    config_file_path = os.environ.get("TRAINTRACK_CENTRAL_CONFIG")
    if config_file_path is None:
        raise ValueError("TRAINTRACK_CENTRAL_CONFIG environment variable is not set")

    logger.success(f"Traintrack central started on {socket.gethostname()}.")
