from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.bootstrap import bootstrap
from app.startup import initialize_runtime
from app.training.jobs.worker import training_worker


@asynccontextmanager
async def app_lifespan(_: FastAPI):
    bootstrap()
    await initialize_runtime(run_model_scan=True)
    training_worker.start()
    try:
        yield
    finally:
        await training_worker.stop()
