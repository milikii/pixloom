from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from PIL import Image

from app.inference import InferenceError, UpscaleRequest


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
            model = self._load_model(path)
            if hasattr(model, "eval"):
                model = model.eval()
            if hasattr(model, "to"):
                model = model.to("cpu")
            self._cache[key] = model
        return self._cache[key]

    def upscale(self, request: UpscaleRequest) -> Image.Image:
        try:
            import torch
            from torchvision.transforms.functional import pil_to_tensor, to_pil_image
        except ImportError as exc:
            raise InferenceError(
                "PyTorch, torchvision, and Spandrel must be installed for the spandrel backend."
            ) from exc

        model = self._load_cached(request.model.absolute_path)
        with Image.open(request.input_path) as image:
            rgb_image = image.convert("RGB")

        scale = request.model.scale
        width, height = rgb_image.size
        tile_size = max(16, request.config.tile_size)
        overlap = max(0, min(request.config.tile_overlap, tile_size // 2))
        output = Image.new("RGB", (width * scale, height * scale))

        for left, top, right, bottom in _iter_tiles(width, height, tile_size, overlap):
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
