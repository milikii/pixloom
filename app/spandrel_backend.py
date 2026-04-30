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

        tensor = pil_to_tensor(rgb_image).float().unsqueeze(0) / 255.0

        with torch.no_grad():
            output = model(tensor)

        if isinstance(output, (list, tuple)):
            output = output[0]
        if isinstance(output, dict):
            output = next(iter(output.values()))
        if output.ndim == 4:
            output = output.squeeze(0)

        output = output.clamp(0, 1).cpu()
        return to_pil_image(output).convert("RGB")
