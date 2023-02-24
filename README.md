# traintrack
Manages and schedules the training jobs on a cluster of machines.


## Development Notes

1. To run the server which is built with [FastAPI](https://fastapi.tiangolo.com/)
   - Development time: `uvicorn traintrack.agent:app --reload`
   - Standalone binary: `python -m traintrack.agent`
