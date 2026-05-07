from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import HTTPException

from app.config import AppConfig
from app.tasks import claim_queued_task, list_tasks, mark_task_completed
from backend.pixloom_api.main import create_app
from backend.pixloom_api.routers import batches, health, models, tasks


def _config(tmp_path: Path) -> AppConfig:
    return AppConfig(
        models_dir=tmp_path / "models",
        bundled_models_dir=tmp_path / "bundled-models",
        input_dir=tmp_path / "input",
        output_dir=tmp_path / "output",
        logs_dir=tmp_path / "logs",
        db_path=tmp_path / "state" / "pixloom.sqlite3",
    )


def test_models_endpoint_lists_operator_models(tmp_path):
    config = _config(tmp_path)
    config.models_dir.mkdir(parents=True)
    (config.models_dir / "SPAN_pretrain.pth").write_bytes(b"fake")

    body = models.get_models(config)

    assert body["hidden_count"] == 0
    assert body["models"][0]["id"] == "span-4x"
    assert body["models"][0]["display_name_zh"] == "SPAN 4x"
    assert body["models"][0]["group_label_zh"] == "照片主力"
    assert body["models"][0]["priority_stars"] == 5


def test_batch_endpoint_enqueues_tasks_and_task_endpoint_lists_them(tmp_path):
    config = _config(tmp_path)
    config.ensure_directories()
    (config.models_dir / "RealESRGAN_x4plus.pth").write_bytes(b"fake")
    input_path = config.input_dir / "source.png"
    input_path.write_bytes(b"fake")

    create_body = batches.create_batch(
        batches.BatchCreateRequest(
            stored_paths=[str(input_path)],
            model_id="realesrgan-x4plus",
            output_format="PNG",
            quality=90,
            output_size_preset="2k",
        ),
        config,
    )

    assert create_body["queued_count"] == 1
    assert create_body["tasks"][0]["status"] == "queued"
    assert create_body["tasks"][0]["output_size_preset"] == "2k"
    assert create_body["tasks"][0]["output_size_label"] == "2K 最长边 2048px"
    assert list_tasks(config)[0].status == "queued"

    list_body = tasks.get_tasks(limit=5, config=config)

    assert list_body["summary"]["queued"] == 1
    assert list_body["tasks"][0]["request_id"] == create_body["first_request_id"]
    assert list_body["tasks"][0]["output_size_preset"] == "2k"
    assert list_body["tasks"][0]["output_size_label"] == "2K 最长边 2048px"


def test_batch_endpoint_defaults_output_size_preset_to_native(tmp_path):
    config = _config(tmp_path)
    config.ensure_directories()
    (config.models_dir / "RealESRGAN_x4plus.pth").write_bytes(b"fake")
    input_path = config.input_dir / "source.png"
    input_path.write_bytes(b"fake")

    create_body = batches.create_batch(
        batches.BatchCreateRequest(
            stored_paths=[str(input_path)],
            model_id="realesrgan-x4plus",
            output_format="PNG",
            quality=90,
        ),
        config,
    )

    assert create_body["queued_count"] == 1
    assert create_body["tasks"][0]["output_size_preset"] == "native"


def test_batch_endpoint_forces_quality_to_100(tmp_path):
    config = _config(tmp_path)
    config.ensure_directories()
    (config.models_dir / "RealESRGAN_x4plus.pth").write_bytes(b"fake")
    input_path = config.input_dir / "source.png"
    input_path.write_bytes(b"fake")

    create_body = batches.create_batch(
        batches.BatchCreateRequest(
            stored_paths=[str(input_path)],
            model_id="realesrgan-x4plus",
            output_format="JPG",
            quality=90,
            output_size_preset="native",
        ),
        config,
    )

    assert create_body["queued_count"] == 1
    assert create_body["tasks"][0]["quality"] == 100


def test_batch_endpoint_rejects_invalid_output_size_preset(tmp_path):
    config = _config(tmp_path)
    config.ensure_directories()
    (config.models_dir / "RealESRGAN_x4plus.pth").write_bytes(b"fake")
    input_path = config.input_dir / "source.png"
    input_path.write_bytes(b"fake")

    with pytest.raises(HTTPException) as exc_info:
        batches.create_batch(
            batches.BatchCreateRequest(
                stored_paths=[str(input_path)],
                model_id="realesrgan-x4plus",
                output_format="PNG",
                quality=90,
                output_size_preset="16k",
            ),
            config,
        )

    detail = exc_info.value.detail

    assert exc_info.value.status_code == 400
    assert detail["code"] == "OUTPUT_SIZE_PRESET_INVALID"
    assert detail["request_id"]
    log_text = next(config.logs_dir.glob("pixloom-*.jsonl")).read_text(encoding="utf-8")
    assert '"event": "ui_rejected"' in log_text


def test_delete_task_endpoint_returns_file_action_details(tmp_path):
    config = _config(tmp_path)
    config.ensure_directories()
    (config.models_dir / "RealESRGAN_x4plus.pth").write_bytes(b"fake")
    input_path = config.input_dir / "source.png"
    output_path = config.output_dir / "result.png"
    input_path.write_bytes(b"input")
    output_path.write_bytes(b"output")
    create_body = batches.create_batch(
        batches.BatchCreateRequest(
            stored_paths=[str(input_path)],
            model_id="realesrgan-x4plus",
            output_format="PNG",
            output_size_preset="native",
        ),
        config,
    )
    request_id = create_body["first_request_id"]
    claim_queued_task(config, request_id)
    mark_task_completed(
        config,
        request_id=request_id,
        output_path=output_path,
        elapsed_seconds=1.2,
    )

    body = tasks.delete_task_endpoint(request_id, config=config)

    assert body["request_id"] == request_id
    assert body["deleted_paths"] == [str(input_path), str(output_path)]
    assert body["missing_paths"] == []
    assert body["skipped_paths"] == []
    assert "已删除任务" in body["message_zh"]


def test_create_app_mounts_frontend_static_export(tmp_path, monkeypatch):
    (tmp_path / "index.html").write_text("<html></html>", encoding="utf-8")
    monkeypatch.setenv("PIXLOOM_FRONTEND_DIST", str(tmp_path))

    app = create_app()

    assert any(getattr(route, "name", "") == "frontend" for route in app.routes)


def test_create_app_syncs_bundled_models_into_runtime_dir(tmp_path, monkeypatch):
    frontend_dir = tmp_path / "frontend-out"
    frontend_dir.mkdir()
    (frontend_dir / "index.html").write_text("<html></html>", encoding="utf-8")
    bundled_dir = tmp_path / "bundled-models"
    bundled_dir.mkdir()
    (bundled_dir / "SPAN_pretrain.pth").write_bytes(b"span")
    runtime_models_dir = tmp_path / "models"

    monkeypatch.setenv("PIXLOOM_FRONTEND_DIST", str(frontend_dir))
    monkeypatch.setenv("PIXLOOM_BUNDLED_MODELS_DIR", str(bundled_dir))
    monkeypatch.setenv("PIXLOOM_MODELS_DIR", str(runtime_models_dir))
    monkeypatch.setenv("PIXLOOM_INPUT_DIR", str(tmp_path / "input"))
    monkeypatch.setenv("PIXLOOM_OUTPUT_DIR", str(tmp_path / "output"))
    monkeypatch.setenv("PIXLOOM_LOGS_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("PIXLOOM_DB_PATH", str(tmp_path / "state" / "pixloom.sqlite3"))

    app = create_app()
    lifespan = app.router.lifespan_context(app)

    async def _run():
        async with lifespan:
            assert runtime_models_dir.joinpath("SPAN_pretrain.pth").read_bytes() == b"span"

    import asyncio

    asyncio.run(_run())


def test_health_endpoint_reports_cpu_only_runtime(tmp_path):
    config = _config(tmp_path)
    config.models_dir.mkdir(parents=True)
    body = health.health_check(
        type("Req", (), {"app": type("App", (), {"state": type("State", (), {"config": config})()})()})()
    )

    assert body["status"] == "ok"
    assert body["runtime"] == "cpu-only"
