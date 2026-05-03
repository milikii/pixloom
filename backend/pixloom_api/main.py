from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import AppConfig, load_config
from app.tasks import initialize_task_store, mark_running_tasks_interrupted

from backend.pixloom_api.routers import (
    batches,
    files,
    health,
    logs,
    models,
    tasks,
    upload,
)
from backend.worker.daemon import BackgroundTaskWorker


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    config = load_config()
    config.ensure_directories()
    initialize_task_store(config)
    mark_running_tasks_interrupted(config)

    worker = BackgroundTaskWorker(config=config)
    worker.start()

    app.state.config = config
    app.state.worker = worker
    yield
    worker.stop()
    worker.join(timeout=30)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Pixloom API",
        version="2.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix="/api")
    app.include_router(models.router, prefix="/api")
    app.include_router(upload.router, prefix="/api")
    app.include_router(batches.router, prefix="/api")
    app.include_router(tasks.router, prefix="/api")
    app.include_router(logs.router, prefix="/api")
    app.include_router(files.router, prefix="/api")

    return app


app = create_app()
