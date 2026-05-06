from __future__ import annotations

from pathlib import Path

from app.config import AppConfig
from app.tasks import list_tasks
from backend.pixloom_api.main import create_app
from backend.pixloom_api.routers import batches, models, tasks


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


def test_batch_endpoint_rejects_invalid_output_size_preset(tmp_path):
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
            output_size_preset="16k",
        ),
        config,
    )

    assert create_body["queued_count"] == 0
    assert "OUTPUT_SIZE_PRESET_INVALID" in create_body["status_message"]


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
