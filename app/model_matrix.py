from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from app.config import AppConfig, load_config
from app.inference import UpscaleResult, run_upscale
from app.model_registry import ModelDefinition, ResolvedModel, list_installed_models


Service = Callable[..., UpscaleResult]


@dataclass(frozen=True)
class ModelMatrixEntry:
    model_id: str
    display_name_zh: str
    backend: str
    input_file: str
    exposure: str
    enabled: bool
    stability_zh: str
    result: str
    elapsed_seconds: float | None = None
    output_path: str = ""
    error_type: str = ""
    error: str = ""


def build_runtime_matrix(
    config: AppConfig,
    image_paths: list[Path],
    *,
    model_ids: set[str] | None = None,
    registry: tuple[ModelDefinition, ...] | None = None,
    service: Service = run_upscale,
) -> list[ModelMatrixEntry]:
    entries: list[ModelMatrixEntry] = []
    models = list_installed_models(config.models_dir, registry)

    for model in models:
        if model_ids is not None and model.id not in model_ids:
            continue
        for image_path in image_paths:
            entry = _evaluate_one(
                config=config,
                image_path=image_path,
                model=model,
                service=service,
            )
            entries.append(entry)
    return entries


def default_input_paths(input_dir: Path, limit: int = 3) -> list[Path]:
    candidates = [
        path
        for path in sorted(input_dir.iterdir())
        if path.is_file() and not path.name.startswith(".")
    ]
    return candidates[:limit]


def format_matrix_markdown(entries: list[ModelMatrixEntry]) -> str:
    lines = [
        "| Model | Backend | Input | Exposure | Enabled | Stability | Result | Elapsed | Output | Error |",
        "|---|---|---|---|---|---|---|---:|---|---|",
    ]
    for entry in entries:
        lines.append(
            "| "
            f"`{entry.display_name_zh or entry.model_id}` | "
            f"`{entry.backend}` | "
            f"`{entry.input_file}` | "
            f"`{entry.exposure}` | "
            f"`{'yes' if entry.enabled else 'no'}` | "
            f"`{entry.stability_zh}` | "
            f"`{entry.result}` | "
            f"`{'' if entry.elapsed_seconds is None else f'{entry.elapsed_seconds:.3f}'}` | "
            f"`{entry.output_path}` | "
            f"`{entry.error_type or entry.error}` |"
        )
    return "\n".join(lines)


def _evaluate_one(
    *,
    config: AppConfig,
    image_path: Path,
    model: ResolvedModel,
    service: Service,
) -> ModelMatrixEntry:
    base = {
        "model_id": model.id,
        "display_name_zh": model.display_name_zh or model.display_name,
        "backend": model.backend,
        "input_file": image_path.name,
        "exposure": model.exposure,
        "enabled": model.enabled,
        "stability_zh": model.stability_zh,
    }

    if model.backend not in {"spandrel"}:
        return ModelMatrixEntry(**base, result="backend-not-implemented")

    try:
        result = service(
            image_path=image_path,
            original_name=image_path.name,
            model=model,
            config=config,
            output_format="PNG",
            quality=90,
        )
        return ModelMatrixEntry(
            **base,
            result="ok",
            elapsed_seconds=result.elapsed_seconds,
            output_path=str(result.output_path),
        )
    except Exception as exc:
        return ModelMatrixEntry(
            **base,
            result="error",
            error_type=type(exc).__name__,
            error=str(exc),
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a local runtime matrix for installed models.")
    parser.add_argument(
        "--input",
        action="append",
        dest="inputs",
        default=[],
        help="Input image path. Repeatable. Defaults to first 3 files under input/.",
    )
    parser.add_argument(
        "--model",
        action="append",
        dest="models",
        default=[],
        help="Model id to evaluate. Repeatable. Defaults to all installed models.",
    )
    args = parser.parse_args()

    config = load_config()
    config.ensure_directories()
    image_paths = [Path(value) for value in args.inputs] or default_input_paths(config.input_dir)
    if not image_paths:
        raise SystemExit("No input images found. Provide --input or place files under input/.")

    model_ids = set(args.models) if args.models else None
    entries = build_runtime_matrix(config, image_paths, model_ids=model_ids)
    print(format_matrix_markdown(entries))


if __name__ == "__main__":
    main()
