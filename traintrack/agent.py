import libtmux
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from traintrack.schema.job import JobDescription, RunJobResponse

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/run")
async def run_job(job: JobDescription):
    print(job.dict())
    return RunJobResponse(
        accepted=True)
