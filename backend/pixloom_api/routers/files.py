"""GET /api/files/output/{path}, GET /api/files/input/{path} — static file serving."""

from __future__ import annotations

import hashlib
from pathlib import Path
import uuid

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse
from PIL import Image, ImageOps, UnidentifiedImageError

router = APIRouter(prefix="/files", tags=["files"])


@router.get("/output/{path:path}")
def serve_output(path: str, request: Request):
    config = request.app.state.config
    resolved = _safe_resolve(config.output_dir, path)
    if resolved is None or not resolved.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(resolved)


@router.get("/output-thumbnail/{path:path}")
def serve_output_thumbnail(
    path: str,
    request: Request,
    size: int = Query(192, ge=32, le=512),
):
    config = request.app.state.config
    resolved = _safe_resolve(config.output_dir, path)
    if resolved is None or not resolved.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    cache_path = _thumbnail_cache_path(
        source=resolved,
        output_root=config.output_dir,
        cache_dir=config.thumbnail_dir,
        size=size,
    )
    if not cache_path.is_file():
        _generate_thumbnail(source=resolved, cache_path=cache_path, size=size)

    return FileResponse(
        cache_path,
        media_type="image/webp",
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )


@router.get("/input/{path:path}")
def serve_input(path: str, request: Request):
    config = request.app.state.config
    resolved = _safe_resolve(config.input_dir, path)
    if resolved is None or not resolved.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(resolved)


def _thumbnail_cache_path(
    source: Path,
    output_root: Path,
    cache_dir: Path,
    size: int,
) -> Path:
    stat = source.stat()
    root_resolved = output_root.resolve()
    relative = source.resolve().relative_to(root_resolved).as_posix()
    key = hashlib.sha256(
        f"{relative}:{stat.st_size}:{stat.st_mtime_ns}:{size}".encode("utf-8")
    ).hexdigest()
    return cache_dir / f"{key}.webp"


def _generate_thumbnail(source: Path, cache_path: Path, size: int) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = cache_path.with_name(f".{cache_path.name}.{uuid.uuid4().hex}.tmp")

    try:
        with Image.open(source) as image:
            image = ImageOps.exif_transpose(image)
            image.thumbnail((size, size), Image.Resampling.LANCZOS)
            if image.mode not in ("RGB", "RGBA"):
                image = image.convert(
                    "RGBA" if "transparency" in image.info else "RGB"
                )
            image.save(tmp_path, format="WEBP", quality=82, method=4)
        tmp_path.replace(cache_path)
    except UnidentifiedImageError as exc:
        raise HTTPException(status_code=415, detail="Unsupported image file") from exc
    finally:
        tmp_path.unlink(missing_ok=True)


def _safe_resolve(root: Path, subpath: str) -> Path | None:
    candidate = (root / subpath).resolve()
    root_resolved = root.resolve()
    try:
        candidate.relative_to(root_resolved)
    except ValueError:
        return None
    return candidate
