from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path

import gradio as gr

from app.config import AppConfig, load_config
from app.inference import InferenceError, UpscaleResult, run_upscale
from app.model_registry import ResolvedModel, list_available_models


Service = Callable[..., UpscaleResult]


def _status(result: UpscaleResult) -> str:
    return (
        f"Model: {result.model_name}\n"
        f"Input: {result.input_size[0]}x{result.input_size[1]}\n"
        f"Output: {result.output_size[0]}x{result.output_size[1]}\n"
        f"Elapsed: {result.elapsed_seconds:.2f}s\n"
        f"Output path: {result.output_path}"
    )


def _model_choices(models: Sequence[ResolvedModel]) -> list[tuple[str, str]]:
    return [(model.display_name, model.id) for model in models]


def handle_upscale(
    image_path: str | None,
    model_id: str,
    output_format: str,
    quality: int,
    config: AppConfig,
    models: Sequence[ResolvedModel],
    service: Service = run_upscale,
) -> tuple[str | None, str | None, str]:
    if not image_path:
        return None, None, "Error: upload an image first."

    try:
        selected = next(model for model in models if model.id == model_id)
        result = service(
            image_path=Path(image_path),
            original_name=Path(image_path).name,
            model=selected,
            config=config,
            output_format=output_format,
            quality=int(quality),
        )
    except StopIteration:
        return None, None, f"Error: selected model is not available: {model_id}"
    except (InferenceError, RuntimeError, ValueError) as exc:
        return None, None, f"Error: {exc}"

    return str(result.output_path), str(result.output_path), _status(result)


def build_demo(config: AppConfig | None = None) -> gr.Blocks:
    runtime_config = config or load_config()
    runtime_config.ensure_directories()
    models = list_available_models(runtime_config.models_dir)
    choices = _model_choices(models)
    default_model = choices[0][1] if choices else None

    with gr.Blocks(title="Pixloom") as demo:
        gr.Markdown("# Pixloom")
        gr.Markdown("CPU-only image upscaling for a self-hosted NAS.")
        with gr.Row():
            with gr.Column():
                image_input = gr.Image(
                    label="Upload image",
                    type="filepath",
                    sources=["upload"],
                )
                model_input = gr.Dropdown(
                    label="Model",
                    choices=choices,
                    value=default_model,
                    interactive=bool(choices),
                )
                output_format = gr.Radio(
                    label="Output format",
                    choices=["PNG", "JPG", "WEBP"],
                    value="PNG",
                )
                quality = gr.Slider(
                    label="JPG/WebP quality",
                    minimum=1,
                    maximum=100,
                    value=90,
                    step=1,
                )
                submit = gr.Button("Upscale", variant="primary")
            with gr.Column():
                preview = gr.Image(label="Preview", type="filepath")
                download = gr.File(label="Download")
                status = gr.Textbox(label="Status", lines=6)

        if choices:
            submit.click(
                fn=lambda image_path, model_id, fmt, q: handle_upscale(
                    image_path=image_path,
                    model_id=model_id,
                    output_format=fmt,
                    quality=q,
                    config=runtime_config,
                    models=models,
                ),
                inputs=[image_input, model_input, output_format, quality],
                outputs=[preview, download, status],
            )
        else:
            status.value = (
                "No installed models found. Place model files in the models directory "
                "and restart the app."
            )

    return demo


def main() -> None:
    config = load_config()
    demo = build_demo(config)
    demo.queue(default_concurrency_limit=1).launch(
        server_name=config.server_name,
        server_port=config.server_port,
        auth=config.gradio_auth,
    )


if __name__ == "__main__":
    main()
