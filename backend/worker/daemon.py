"""Background worker daemon that polls SQLite and processes queued tasks."""

from __future__ import annotations

import threading
import time
from pathlib import Path

from app.config import AppConfig
from app.inference import run_upscale, BackendRunner
from app.model_registry import get_default_registry, resolve_model, ModelNotFoundError
from app.tasks import (
    claim_next_queued_task,
    mark_task_completed,
    mark_task_failed,
    update_task_progress,
)


class BackgroundTaskWorker:
    """Serial background worker that claims and processes one task at a time."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="pixloom-worker")
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    def join(self, timeout: float | None = None) -> None:
        if self._thread is not None:
            self._thread.join(timeout=timeout)

    def _run(self) -> None:
        registry = get_default_registry()
        runner = BackendRunner()

        while not self._stop_event.is_set():
            task = claim_next_queued_task(self._config)
            if task is None:
                self._stop_event.wait(timeout=2.0)
                continue

            try:
                self._process_task(task, registry, runner)
            except Exception:
                pass

    def _process_task(self, task, registry, runner) -> None:
        def on_progress(step: str, value: float) -> None:
            try:
                update_task_progress(self._config, task.request_id, step, value)
            except Exception:
                pass

        on_progress("正在准备模型", 0.05)

        try:
            model = resolve_model(
                task.model_id,
                self._config.models_dir,
                registry=registry,
            )
        except ModelNotFoundError as exc:
            mark_task_failed(
                self._config,
                task.request_id,
                error_code="MODEL_NOT_FOUND",
                error_detail=str(exc),
            )
            return

        on_progress("正在推理", 0.15)

        try:
            result = run_upscale(
                image_path=task.input_path,
                original_name=task.input_filename,
                model=model,
                config=self._config,
                output_format=task.output_format,
                quality=task.quality,
                backend=runner,
                request_id=task.request_id,
                progress_callback=on_progress,
                pre_persisted_input=True,
                keep_input_on_failure=True,
            )
        except Exception as exc:
            code = getattr(exc, "code", "INFERENCE_FAILED")
            mark_task_failed(
                self._config,
                task.request_id,
                error_code=code,
                error_detail=str(exc),
            )
            return

        mark_task_completed(
            self._config,
            task.request_id,
            output_path=result.output_path,
            elapsed_seconds=result.elapsed_seconds,
        )
