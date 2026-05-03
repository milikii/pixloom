from __future__ import annotations

from pathlib import Path

from PIL import Image

from app.config import AppConfig
from app.inference import UpscaleResult
from app.model_matrix import build_runtime_matrix, default_input_paths, format_matrix_markdown
from app.model_registry import ModelDefinition


def _config(tmp_path: Path) -> AppConfig:
    return AppConfig(
        models_dir=tmp_path / "models",
        input_dir=tmp_path / "input",
        output_dir=tmp_path / "output",
        logs_dir=tmp_path / "logs",
        db_path=tmp_path / "state" / "pixloom.sqlite3",
    )


def test_default_input_paths_returns_first_files(tmp_path):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    for name in ["b.png", "a.png", ".keep", "c.png"]:
        path = input_dir / name
        if name.startswith("."):
            path.write_text("")
        else:
            Image.new("RGB", (4, 4)).save(path)

    paths = default_input_paths(input_dir, limit=2)

    assert [path.name for path in paths] == ["a.png", "b.png"]


def test_build_runtime_matrix_marks_backend_not_implemented(tmp_path):
    config = _config(tmp_path)
    config.models_dir.mkdir(parents=True)
    config.input_dir.mkdir(parents=True)
    image_path = config.input_dir / "sample.png"
    Image.new("RGB", (4, 4)).save(image_path)
    model_path = config.models_dir / "apisr.onnx"
    model_path.write_bytes(b"fake")

    registry = (
        ModelDefinition(
            id="apisr",
            display_name="APISR",
            backend="onnxruntime",
            architecture="APISR",
            scale=4,
            path=Path("apisr.onnx"),
            image_types=("anime",),
            notes="test",
            enabled=False,
            exposure="evaluation",
            display_name_zh="APISR",
            stability_zh="未启用",
        ),
    )

    entries = build_runtime_matrix(config, [image_path], registry=registry)

    assert len(entries) == 1
    assert entries[0].result == "backend-not-implemented"


def test_build_runtime_matrix_records_success(tmp_path):
    config = _config(tmp_path)
    config.models_dir.mkdir(parents=True)
    config.input_dir.mkdir(parents=True)
    image_path = config.input_dir / "sample.png"
    Image.new("RGB", (4, 4)).save(image_path)
    model_path = config.models_dir / "model.pth"
    model_path.write_bytes(b"fake")

    registry = (
        ModelDefinition(
            id="fake-4x",
            display_name="Fake 4x",
            backend="spandrel",
            architecture="FakeSR",
            scale=4,
            path=Path("model.pth"),
            image_types=("test",),
            notes="test",
            enabled=True,
            exposure="evaluation",
            display_name_zh="Fake 4x 中文",
            stability_zh="待本机验收",
        ),
    )

    def fake_service(**kwargs):
        output = config.output_dir / "result.png"
        output.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (16, 16)).save(output)
        return UpscaleResult(
            input_path=kwargs["image_path"],
            output_path=output,
            input_size=(4, 4),
            output_size=(16, 16),
            model_name="Fake 4x 中文",
            elapsed_seconds=1.5,
        )

    entries = build_runtime_matrix(
        config,
        [image_path],
        registry=registry,
        service=fake_service,
    )

    assert len(entries) == 1
    assert entries[0].result == "ok"
    assert entries[0].elapsed_seconds == 1.5
    assert entries[0].output_path.endswith("result.png")


def test_format_matrix_markdown_renders_rows():
    markdown = format_matrix_markdown([])

    assert "Model" in markdown
    assert "Result" in markdown
