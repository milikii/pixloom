from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from PIL import Image

from app.app import format_model_guidance, handle_batch_upscale, handle_upscale
from app.config import AppConfig
from app.inference import InferenceError, UpscaleResult
from app.model_registry import ResolvedModel
from app.tasks import list_tasks


class FakeService:
    def __init__(self, result: UpscaleResult | Exception):
        self.result = result
        self.calls = []

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        if isinstance(self.result, Exception):
            raise self.result
        return replace(
            self.result,
            input_path=kwargs["image_path"],
            request_id=kwargs["request_id"],
        )


class BatchFakeService:
    def __init__(self, tmp_path: Path, fail_filenames: set[str] | None = None):
        self.tmp_path = tmp_path
        self.fail_filenames = fail_filenames or set()
        self.calls = []

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        if kwargs["original_name"] in self.fail_filenames:
            raise InferenceError(
                code="BACKEND_FAILURE",
                user_message_zh="放大失败。",
                likely_cause_zh="后端在推理阶段崩溃。",
                suggested_action_zh="请更换模型或稍后再试。",
                detail=f"failed {kwargs['original_name']}",
                request_id=kwargs["request_id"],
            )
        output_path = self.tmp_path / f"{kwargs['request_id']}.png"
        Image.new("RGB", (32, 24)).save(output_path)
        return UpscaleResult(
            input_path=kwargs["image_path"],
            output_path=output_path,
            input_size=(8, 6),
            output_size=(32, 24),
            model_name="Fake 4x 中文",
            elapsed_seconds=1.25,
            request_id=kwargs["request_id"],
        )


def _model(tmp_path: Path) -> ResolvedModel:
    model_path = tmp_path / "model.pth"
    model_path.write_bytes(b"fake")
    return ResolvedModel(
        id="fake-4x",
        display_name="Fake 4x",
        backend="spandrel",
        architecture="FakeSR",
        scale=4,
        path=Path("model.pth"),
        absolute_path=model_path,
        image_types=("test",),
        notes="test",
        display_name_zh="Fake 4x 中文",
        recommended_for_zh="适合测试、通用小图和功能验证。",
        warning_zh="测试环境专用模型，请勿用于真实质量判断。",
    )


def _config(tmp_path: Path) -> AppConfig:
    return AppConfig(
        models_dir=tmp_path,
        input_dir=tmp_path / "input",
        output_dir=tmp_path / "output",
        logs_dir=tmp_path / "logs",
        db_path=tmp_path / "state" / "pixloom.sqlite3",
    )


def test_handle_upscale_returns_preview_download_and_status(tmp_path, tiny_png):
    output_path = tmp_path / "output.png"
    Image.new("RGB", (32, 24)).save(output_path)
    result = UpscaleResult(
        input_path=tiny_png,
        output_path=output_path,
        input_size=(8, 6),
        output_size=(32, 24),
        model_name="Fake 4x 中文",
        elapsed_seconds=1.25,
        request_id="req-1234",
    )
    service = FakeService(result)
    config = _config(tmp_path)

    preview, download, status, request_log = handle_upscale(
        image_path=str(tiny_png),
        model_id="fake-4x",
        output_format="PNG",
        quality=90,
        config=config,
        models=[_model(tmp_path)],
        service=service,
    )

    assert preview == str(output_path)
    assert download == str(output_path)
    request_id = service.calls[0]["request_id"]
    assert f"请求编号：{request_id}" in status
    assert "Fake 4x 中文" in status
    assert "输入尺寸：8x6" in status
    assert "输出尺寸：32x24" in status
    assert "1.25 秒" in status
    assert len(service.calls) == 1
    assert service.calls[0]["image_path"].parent == config.input_dir
    assert service.calls[0]["image_path"].name.endswith(f"_{tiny_png.name}")
    assert service.calls[0]["image_path"].is_file()
    assert service.calls[0]["original_name"] == tiny_png.name
    assert service.calls[0]["model"] == _model(tmp_path)
    assert service.calls[0]["config"] == config
    assert service.calls[0]["output_format"] == "PNG"
    assert service.calls[0]["quality"] == 90
    assert service.calls[0]["request_id"]
    assert "[queued] task_queued" in request_log
    assert "[completed] task_completed" in request_log
    tasks = list_tasks(config)
    assert len(tasks) == 1
    assert tasks[0].request_id == request_id
    assert tasks[0].status == "completed"
    assert tasks[0].output_path == output_path


def test_handle_batch_upscale_records_one_batch_for_multiple_images(tmp_path, tiny_png):
    second = tmp_path / "second.png"
    Image.new("RGB", (8, 6)).save(second)
    service = BatchFakeService(tmp_path)
    config = _config(tmp_path)

    preview, download, status, request_log = handle_batch_upscale(
        image_paths=[str(tiny_png), str(second)],
        model_id="fake-4x",
        output_format="PNG",
        quality=90,
        config=config,
        models=[_model(tmp_path)],
        service=service,
    )

    tasks = list_tasks(config)
    assert preview == download
    assert preview is not None
    assert "总数：2" in status
    assert "已完成：2" in status
    assert "失败：0" in status
    assert len(service.calls) == 2
    assert len(tasks) == 2
    assert {task.status for task in tasks} == {"completed"}
    assert len({task.batch_id for task in tasks}) == 1
    assert "[completed] task_completed" in request_log


def test_handle_batch_upscale_keeps_processing_after_one_failure(tmp_path, tiny_png):
    bad = tmp_path / "bad.png"
    Image.new("RGB", (8, 6)).save(bad)
    service = BatchFakeService(tmp_path, fail_filenames={"bad.png"})
    config = _config(tmp_path)

    preview, download, status, request_log = handle_batch_upscale(
        image_paths=[str(tiny_png), str(bad)],
        model_id="fake-4x",
        output_format="PNG",
        quality=90,
        config=config,
        models=[_model(tmp_path)],
        service=service,
    )

    tasks = list_tasks(config)
    statuses = {task.input_filename: task.status for task in tasks}
    assert preview == download
    assert preview is not None
    assert "总数：2" in status
    assert "已完成：1" in status
    assert "失败：1" in status
    assert len(service.calls) == 2
    assert statuses[tiny_png.name] == "completed"
    assert statuses["bad.png"] == "failed"
    assert len({task.batch_id for task in tasks}) == 1
    assert "BACKEND_FAILURE" in request_log


def test_handle_upscale_maps_error_to_status(tmp_path, tiny_png):
    service = FakeService(
        InferenceError(
            code="BACKEND_FAILURE",
            user_message_zh="放大失败。",
            likely_cause_zh="后端在推理阶段崩溃。",
            suggested_action_zh="请更换模型或稍后再试。",
            detail="boom",
            request_id="req-failed",
        )
    )

    preview, download, status, request_log = handle_upscale(
        image_path=str(tiny_png),
        model_id="fake-4x",
        output_format="PNG",
        quality=90,
        config=_config(tmp_path),
        models=[_model(tmp_path)],
        service=service,
    )

    assert preview is None
    assert download is None
    assert "请求编号：req-failed" in status
    assert "错误代码：BACKEND_FAILURE" in status
    assert "后端在推理阶段崩溃" in status
    assert "BACKEND_FAILURE" in request_log
    assert len(service.calls) == 1
    tasks = list_tasks(_config(tmp_path))
    assert len(tasks) == 1
    assert tasks[0].status == "failed"
    assert tasks[0].error_code == "BACKEND_FAILURE"


def test_handle_upscale_rejects_missing_image(tmp_path):
    preview, download, status, request_log = handle_upscale(
        image_path=None,
        model_id="fake-4x",
        output_format="PNG",
        quality=90,
        config=_config(tmp_path),
        models=[],
    )

    assert preview is None
    assert download is None
    assert "请先上传图片再开始放大" in status
    assert "错误代码：NO_IMAGE_SELECTED" in status
    assert "NO_IMAGE_SELECTED" in request_log


def test_handle_upscale_rejects_unknown_model_id(tmp_path, tiny_png):
    preview, download, status, request_log = handle_upscale(
        image_path=str(tiny_png),
        model_id="missing",
        output_format="PNG",
        quality=90,
        config=_config(tmp_path),
        models=[_model(tmp_path)],
    )

    assert preview is None
    assert download is None
    assert "错误代码：MODEL_NOT_AVAILABLE" in status
    assert "当前选择的模型不可用" in status
    assert "MODEL_NOT_AVAILABLE" in request_log


def test_handle_upscale_maps_unexpected_runtime_error_to_status(tmp_path, tiny_png):
    preview, download, status, request_log = handle_upscale(
        image_path=str(tiny_png),
        model_id="fake-4x",
        output_format="PNG",
        quality=90,
        config=_config(tmp_path),
        models=[_model(tmp_path)],
        service=FakeService(RuntimeError("boom")),
    )

    assert preview is None
    assert download is None
    assert "错误代码：UNEXPECTED_UI_FAILURE" in status
    assert "请求编号：" in status
    assert "UNEXPECTED_UI_FAILURE" in request_log


def test_format_model_guidance_returns_chinese_text(tmp_path):
    guidance = format_model_guidance("fake-4x", [_model(tmp_path)])

    assert "模型说明" in guidance
    assert "适合测试、通用小图和功能验证" in guidance
    assert "测试环境专用模型" in guidance
