from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from app.inference import InferenceError, UpscaleRequest


def _dependency_error() -> InferenceError:
    return InferenceError(
        code="ONNXRUNTIME_DEPENDENCY_MISSING",
        user_message_zh="当前 ONNX 推理依赖不可用。",
        likely_cause_zh="运行环境缺少 onnxruntime。",
        suggested_action_zh="请重建 Docker 镜像或重新安装 onnxruntime 后再试。",
        detail="onnxruntime must be installed for the ONNX backend.",
    )


def _default_session_factory(path: Path) -> Any:
    try:
        import onnxruntime as ort
    except ImportError as exc:
        raise _dependency_error() from exc
    return ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])


class OnnxRuntimeBackend:
    def __init__(self, session_factory: Callable[[Path], Any] | None = None) -> None:
        self._session_factory = session_factory or _default_session_factory
        self._cache: dict[tuple[str, int, int], Any] = {}

    def _load_cached(self, path: Path) -> Any:
        stat = path.stat()
        key = (str(path.resolve()), stat.st_mtime_ns, stat.st_size)
        if key not in self._cache:
            self._cache[key] = self._session_factory(path)
        return self._cache[key]

    def upscale(self, request: UpscaleRequest, progress_callback=None) -> Image.Image:
        session = self._load_cached(request.model.absolute_path)
        input_name = session.get_inputs()[0].name

        with Image.open(request.input_path) as image:
            rgb_image = image.convert("RGB")

        width, height = rgb_image.size
        scale = max(1, request.model.scale)
        output = Image.new("RGB", (width * scale, height * scale))
        tiles = _iter_tiles(width, height, max(16, request.config.tile_size), max(0, request.config.tile_overlap))
        total_tiles = len(tiles)

        for index, (left, top, right, bottom) in enumerate(tiles, start=1):
            if progress_callback is not None:
                progress = 0.15 + ((index - 1) / max(1, total_tiles)) * 0.7
                progress_callback(f"正在处理 ONNX 分块 {index}/{total_tiles}", progress)

            tile = rgb_image.crop((left, top, right, bottom))
            tile_array = np.asarray(tile).astype("float32") / 255.0
            tile_array = np.transpose(tile_array, (2, 0, 1))[None, ...]
            tile_output = session.run(None, {input_name: tile_array})[0]
            if tile_output.ndim == 4:
                tile_output = tile_output[0]

            tile_output = np.clip(tile_output, 0.0, 1.0)
            tile_output = np.transpose(tile_output, (1, 2, 0))
            tile_image = Image.fromarray((tile_output * 255.0).round().astype("uint8"))

            paste_left = left * scale
            paste_top = top * scale
            output.paste(tile_image, (paste_left, paste_top))

        if progress_callback is not None:
            progress_callback("ONNX 推理完成，准备返回结果", 0.9)
        return output


def _iter_tiles(width: int, height: int, tile_size: int, overlap: int) -> list[tuple[int, int, int, int]]:
    overlap = min(overlap, tile_size // 2)
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
