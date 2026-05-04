from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from app.config import AppConfig
from app.inference import (
    BackendRunner,
    InferenceError,
    UpscaleRequest,
    run_upscale,
    validate_upload,
)
from app.model_registry import ResolvedModel


class FakeBackend:
    def upscale(self, request: UpscaleRequest):
        with Image.open(request.input_path) as image:
            resized = image.resize(
                (image.width * request.model.scale, image.height * request.model.scale)
            )
        return resized


class FailingBackend:
    def upscale(self, request: UpscaleRequest):
        raise RuntimeError("backend exploded")


class SaveFailingBackend:
    def upscale(self, request: UpscaleRequest):
        with Image.open(request.input_path) as image:
            return image.resize(
                (image.width * request.model.scale, image.height * request.model.scale)
            )


def _model(
    tmp_path: Path,
    backend: str = "spandrel",
    *,
    architecture: str = "FakeSR",
    scale: int = 4,
    filename: str = "model.pth",
    model_id: str = "fake-4x",
) -> ResolvedModel:
    model_path = tmp_path / filename
    model_path.write_bytes(b"fake")
    return ResolvedModel(
        id=model_id,
        display_name="Fake 4x",
        backend=backend,  # type: ignore[arg-type]
        architecture=architecture,
        scale=scale,
        path=Path(filename),
        absolute_path=model_path,
        image_types=("test",),
        notes="test",
        display_name_zh="Fake 4x 中文",
        recommended_for_zh="适合测试图片。",
        warning_zh="测试提示。",
    )


def _runtime_config(tmp_path: Path, **overrides) -> AppConfig:
    values = {
        "input_dir": tmp_path / "input",
        "output_dir": tmp_path / "output",
        "logs_dir": tmp_path / "logs",
        "db_path": tmp_path / "state" / "pixloom.sqlite3",
    }
    values.update(overrides)
    return AppConfig(**values)


def test_validate_upload_accepts_supported_images(tmp_path, tiny_png):
    result = validate_upload(tiny_png, AppConfig(input_dir=tmp_path))

    assert result.width == 8
    assert result.height == 6
    assert result.format == "PNG"


def test_validate_upload_rejects_unsupported_extension(tmp_path):
    path = tmp_path / "sample.gif"
    Image.new("RGB", (4, 4)).save(path)

    with pytest.raises(InferenceError, match="Supported formats"):
        validate_upload(path, AppConfig(input_dir=tmp_path))


def test_validate_upload_rejects_fake_image(tmp_path):
    path = tmp_path / "fake.png"
    path.write_text("not an image", encoding="utf-8")

    with pytest.raises(InferenceError, match="could not be decoded"):
        validate_upload(path, AppConfig(input_dir=tmp_path))


def test_validate_upload_rejects_large_image(tmp_path):
    path = tmp_path / "large.png"
    Image.new("RGB", (9, 4)).save(path)

    config = AppConfig(input_dir=tmp_path, max_input_side=8)

    with pytest.raises(InferenceError, match="exceeds the maximum input side"):
        validate_upload(path, config)


def test_validate_upload_rejects_oversized_file_before_decode(tmp_path):
    path = tmp_path / "large.png"
    path.write_bytes(b"x" * 11)

    config = AppConfig(input_dir=tmp_path, max_upload_bytes=10)

    with pytest.raises(InferenceError, match="maximum upload size"):
        validate_upload(path, config)


def test_run_upscale_with_fake_backend_writes_output(tmp_path, tiny_png):
    config = _runtime_config(
        tmp_path,
        max_output_side=64,
    )

    progress_events = []
    result = run_upscale(
        image_path=tiny_png,
        original_name="sample.png",
        model=_model(tmp_path),
        config=config,
        output_format="PNG",
        quality=90,
        backend=FakeBackend(),
        progress_callback=lambda step, value: progress_events.append((step, value)),
    )

    assert result.input_size == (8, 6)
    assert result.output_size == (32, 24)
    assert result.model_name == "Fake 4x 中文"
    assert result.output_path.is_file()
    assert result.elapsed_seconds >= 0
    assert result.request_id
    assert progress_events
    assert progress_events[0][0] == "准备开始推理"
    assert progress_events[-1][0] == "处理完成"

    log_files = list(config.logs_dir.glob("pixloom-*.jsonl"))
    assert len(log_files) == 1
    log_text = log_files[0].read_text(encoding="utf-8")
    assert '"event": "request_succeeded"' in log_text
    assert result.request_id in log_text
    assert '"input_path":' in log_text
    assert str(result.input_path) in log_text


def test_run_upscale_rejects_too_large_output(tmp_path, tiny_png):
    config = _runtime_config(
        tmp_path,
        max_output_side=16,
    )

    with pytest.raises(InferenceError, match="exceeds the maximum output side"):
        run_upscale(
            image_path=tiny_png,
            original_name="sample.png",
            model=_model(tmp_path),
            config=config,
            output_format="PNG",
            quality=90,
            backend=FakeBackend(),
        )


def test_run_upscale_target_size_preset_writes_requested_longest_side(tmp_path, tiny_png):
    config = _runtime_config(
        tmp_path,
        max_output_side=4096,
    )

    result = run_upscale(
        image_path=tiny_png,
        original_name="sample.png",
        model=_model(tmp_path),
        config=config,
        output_format="PNG",
        quality=90,
        backend=FakeBackend(),
        output_size_preset="2k",
    )

    assert result.output_size == (2048, 1536)
    assert result.output_size_preset == "2k"
    assert result.target_longest_side == 2048
    assert "_2k." in result.output_path.name
    assert not list(config.input_dir.glob("*prepared*"))

    log_text = next(config.logs_dir.glob("pixloom-*.jsonl")).read_text(encoding="utf-8")
    assert '"output_size_preset": "2k"' in log_text
    assert '"target_longest_side": 2048' in log_text
    assert '"output_dimensions": {"width": 2048, "height": 1536}' in log_text


def test_run_upscale_rejects_target_preset_over_output_limit(tmp_path, tiny_png):
    config = _runtime_config(
        tmp_path,
        max_output_side=1024,
    )

    with pytest.raises(InferenceError, match="exceeds the maximum output side"):
        run_upscale(
            image_path=tiny_png,
            original_name="sample.png",
            model=_model(tmp_path),
            config=config,
            output_format="PNG",
            quality=90,
            backend=FakeBackend(),
            output_size_preset="2k",
        )


def test_run_upscale_cleans_prepared_input_when_backend_fails(tmp_path, tiny_png):
    config = _runtime_config(
        tmp_path,
        max_output_side=4096,
    )

    with pytest.raises(InferenceError):
        run_upscale(
            image_path=tiny_png,
            original_name="sample.png",
            model=_model(tmp_path),
            config=config,
            output_format="PNG",
            quality=90,
            backend=FailingBackend(),
            output_size_preset="2k",
        )

    assert not list(config.input_dir.glob("*prepared*"))


def test_run_upscale_rejects_invalid_output_format_before_persisting_input(
    tmp_path, tiny_png
):
    config = _runtime_config(tmp_path)

    with pytest.raises(InferenceError, match="Output format must be PNG, JPG, JPEG, or WEBP."):
        run_upscale(
            image_path=tiny_png,
            original_name="sample.png",
            model=_model(tmp_path),
            config=config,
            output_format="TIFF",
            quality=90,
            backend=FakeBackend(),
        )

    assert list(config.input_dir.iterdir()) == []


def test_run_upscale_maps_backend_failure_to_readable_error(tmp_path, tiny_png):
    config = _runtime_config(tmp_path)

    with pytest.raises(InferenceError) as exc_info:
        run_upscale(
            image_path=tiny_png,
            original_name="sample.png",
            model=_model(tmp_path),
            config=config,
            output_format="PNG",
            quality=90,
            backend=FailingBackend(),
        )

    exc = exc_info.value
    assert exc.code == "UPSCALE_FAILED"
    assert exc.request_id
    assert "放大处理失败" in exc.user_message_zh
    assert list(config.input_dir.iterdir()) == []
    log_files = list(config.logs_dir.glob("pixloom-*.jsonl"))
    assert len(log_files) == 1
    log_text = log_files[0].read_text(encoding="utf-8")
    assert '"status": "failure"' in log_text
    assert exc.request_id in log_text


def test_default_backend_runner_delegates_to_onnx_backend(monkeypatch, tmp_path, tiny_png):
    from app import onnx_backend

    class FakeOnnxBackend:
        def upscale(self, request: UpscaleRequest):
            with Image.open(request.input_path) as image:
                return image.resize((image.width * 4, image.height * 4))

    monkeypatch.setattr(onnx_backend, "OnnxRuntimeBackend", FakeOnnxBackend)
    config = _runtime_config(tmp_path)

    result = run_upscale(
        image_path=tiny_png,
        original_name="sample.png",
        model=_model(
            tmp_path,
            backend="onnxruntime",
            architecture="APISR",
            filename="model.onnx",
            model_id="apisr-4x-int8",
        ),
        config=config,
        output_format="PNG",
        quality=90,
        backend=BackendRunner(),
    )

    assert result.output_size == (32, 24)


def test_default_backend_runner_delegates_to_spandrel_backend(monkeypatch, tmp_path, tiny_png):
    from app import spandrel_backend

    class FakeSpandrelBackend:
        def upscale(self, request: UpscaleRequest):
            with Image.open(request.input_path) as image:
                return image.resize((image.width * 4, image.height * 4))

    monkeypatch.setattr(spandrel_backend, "SpandrelBackend", FakeSpandrelBackend)

    config = _runtime_config(tmp_path)

    result = run_upscale(
        image_path=tiny_png,
        original_name="sample.png",
        model=_model(tmp_path, backend="spandrel"),
        config=config,
        output_format="PNG",
        quality=90,
        backend=BackendRunner(),
    )

    assert result.output_size == (32, 24)


def test_default_backend_runner_delegates_to_face_restoration_backend(monkeypatch, tmp_path, tiny_png):
    from app import face_restoration_backend

    class FakeFaceBackend:
        def upscale(self, request: UpscaleRequest):
            with Image.open(request.input_path) as image:
                return image.copy()

    monkeypatch.setattr(
        face_restoration_backend,
        "FaceRestorationBackend",
        FakeFaceBackend,
    )

    config = _runtime_config(tmp_path)

    result = run_upscale(
        image_path=tiny_png,
        original_name="sample.png",
        model=_model(
            tmp_path,
            backend="custom",
            architecture="CodeFormer",
            scale=1,
            model_id="codeformer",
        ),
        config=config,
        output_format="PNG",
        quality=90,
        backend=BackendRunner(),
    )

    assert result.output_size == (8, 6)


def test_run_upscale_rolls_back_files_when_save_fails(tmp_path, tiny_png, monkeypatch):
    config = _runtime_config(tmp_path)

    def fail_save(*args, **kwargs):
        output_path = args[1]
        output_path.write_bytes(b"partial")
        raise OSError("disk full")

    monkeypatch.setattr("app.inference._save_image", fail_save)

    with pytest.raises(InferenceError) as exc_info:
        run_upscale(
            image_path=tiny_png,
            original_name="sample.png",
            model=_model(tmp_path),
            config=config,
            output_format="PNG",
            quality=90,
            backend=SaveFailingBackend(),
        )

    exc = exc_info.value
    assert exc.code == "OUTPUT_SAVE_FAILED"
    assert "保存结果文件失败" in exc.user_message_zh
    assert list(config.input_dir.iterdir()) == []
    assert list(config.output_dir.iterdir()) == []
