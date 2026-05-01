from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from PIL import Image

from app.inference import InferenceError, UpscaleRequest


def _dependency_error() -> InferenceError:
    return InferenceError(
        code="SPANDREL_DEPENDENCY_MISSING",
        user_message_zh="当前 Spandrel 推理依赖不可用。",
        likely_cause_zh="运行环境缺少 PyTorch、torchvision 或 Spandrel。",
        suggested_action_zh="请重新安装依赖或重建 Docker 镜像后再试。",
        detail="PyTorch, torchvision, and Spandrel must be installed for the spandrel backend.",
    )


def _default_load_model(path: Path) -> Any:
    from spandrel import ModelLoader

    return ModelLoader().load_from_file(str(path))


class SpandrelBackend:
    def __init__(self, load_model: Callable[[Path], Any] | None = None) -> None:
        self._load_model = load_model or _default_load_model
        self._cache: dict[tuple[str, int, int], Any] = {}

    def _load_cached(self, path: Path) -> Any:
        stat = path.stat()
        key = (str(path.resolve()), stat.st_mtime_ns, stat.st_size)
        if key not in self._cache:
            try:
                model = self._load_model(path)
            except ImportError as exc:
                raise _dependency_error() from exc
            if hasattr(model, "eval"):
                model = model.eval()
            if hasattr(model, "to"):
                model = model.to("cpu")
            self._cache[key] = model
        return self._cache[key]

    def upscale(self, request: UpscaleRequest, progress_callback=None) -> Image.Image:
        try:
            import torch
            from torchvision.transforms.functional import pil_to_tensor, to_pil_image
        except ImportError as exc:
            raise _dependency_error() from exc

        model = self._load_cached(request.model.absolute_path)
        with Image.open(request.input_path) as image:
            rgb_image = image.convert("RGB")

        scale = request.model.scale
        width, height = rgb_image.size
        tile_size = max(16, request.config.tile_size)
        overlap = max(0, min(request.config.tile_overlap, tile_size // 2))
        output = Image.new("RGB", (width * scale, height * scale))
        tiles = _iter_tiles(width, height, tile_size, overlap)
        total_tiles = len(tiles)

        for index, (left, top, right, bottom) in enumerate(tiles, start=1):
            if progress_callback is not None:
                progress = 0.15 + ((index - 1) / max(1, total_tiles)) * 0.7
                progress_callback(f"正在处理分块 {index}/{total_tiles}", progress)
            tile = rgb_image.crop((left, top, right, bottom))
            tensor = pil_to_tensor(tile).float().unsqueeze(0) / 255.0

            with torch.no_grad():
                tile_output = model(tensor)

            if isinstance(tile_output, (list, tuple)):
                tile_output = tile_output[0]
            if isinstance(tile_output, dict):
                tile_output = next(iter(tile_output.values()))
            if tile_output.ndim == 4:
                tile_output = tile_output.squeeze(0)

            tile_image = to_pil_image(tile_output.clamp(0, 1).cpu()).convert("RGB")
            paste_left = left * scale
            paste_top = top * scale
            output.paste(tile_image, (paste_left, paste_top))

        if progress_callback is not None:
            progress_callback("推理完成，准备返回结果", 0.9)
        return output


def _iter_tiles(
    width: int,
    height: int,
    tile_size: int,
    overlap: int,
) -> list[tuple[int, int, int, int]]:
    step = max(1, tile_size - overlap)
    x_positions = _positions(width, tile_size, step)
    y_positions = _positions(height, tile_size, step)
    return [
        (x, y, min(x + tile_size, width), min(y + tile_size, height))
        for y in y_positions
        for x in x_positions
    ]


def _positions(length: int, tile_size: int, step: int) -> list[int]:
    if length <= tile_size:
        return [0]
    positions = list(range(0, length - tile_size + 1, step))
    final = length - tile_size
    if positions[-1] != final:
        positions.append(final)
    return positions
