"""Background worker daemon that polls SQLite and processes queued tasks."""

from __future__ import annotations

import sys
import threading
import traceback

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
        def _log(msg):
            print(f"[pixloom-worker] {msg}", file=sys.stderr, flush=True)

        _log("thread started")
        try:
            registry = get_default_registry()
            _log(f"registry loaded ({len(registry)} models)")
        except Exception as exc:
            _log(f"FATAL registry: {exc}")
            traceback.print_exc(file=sys.stderr)
            return
        runner = BackendRunner()
        _log("backend runner ready, entering loop")

        while not self._stop_event.is_set():
            try:
                task = claim_next_queued_task(self._config)
            except Exception as exc:
                _log(f"claim error: {exc}")
                self._stop_event.wait(timeout=2.0)
                continue

            if task is None:
                self._stop_event.wait(timeout=2.0)
                continue

            _log(f"processing {task.request_id[:30]} model={task.model_id}")
            try:
                self._process_task(task, registry, runner)
            except Exception as exc:
                _log(f"CRASH processing task: {exc}")
                traceback.print_exc(file=sys.stderr)
                try:
                    mark_task_failed(
                        self._config,
                        request_id=task.request_id,
                        error_code="WORKER_CRASH",
                        error_detail=str(exc),
                    )
                except Exception:
                    pass

    def _process_task(self, task, registry, runner) -> None:
        def on_progress(step: str, value: float) -> None:
            try:
                update_task_progress(
                    self._config,
                    request_id=task.request_id,
                    progress_step=step,
                    progress_value=value,
                )
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
                request_id=task.request_id,
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
                output_size_preset=task.output_size_preset,
            )
        except Exception as exc:
            code = getattr(exc, "code", "INFERENCE_FAILED")
            detail = f"{exc.__class__.__name__}: {exc}"
            if exc.__cause__:
                detail += f" | caused by: {exc.__cause__.__class__.__name__}: {exc.__cause__}"
            print(f"[pixloom-worker] FAILED: {detail}", file=sys.stderr, flush=True)
            traceback.print_exc(file=sys.stderr)
            mark_task_failed(
                self._config,
                request_id=task.request_id,
                error_code=code,
                error_detail=detail,
            )
            return

        mark_task_completed(
            self._config,
            request_id=task.request_id,
            output_path=result.output_path,
            elapsed_seconds=result.elapsed_seconds,
        )
