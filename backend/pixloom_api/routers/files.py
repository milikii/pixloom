"""GET /api/files/* and POST /api/files/output-archive — file serving."""

from __future__ import annotations

from pathlib import Path
import tempfile
from time import strftime
import uuid
import zipfile

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse
from PIL import Image, ImageOps, UnidentifiedImageError
from pydantic import BaseModel, Field
from starlette.background import BackgroundTask

from app.storage import thumbnail_cache_path
from app.tasks import get_task

router = APIRouter(prefix="/files", tags=["files"])


class OutputArchiveRequest(BaseModel):
    request_ids: list[str] = Field(min_length=1, max_length=200)


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

    cache_path = thumbnail_cache_path(config=config, source=resolved, size=size)
    if not cache_path.is_file():
        _generate_thumbnail(source=resolved, cache_path=cache_path, size=size)

    return FileResponse(
        cache_path,
        media_type="image/webp",
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )


@router.post("/output-archive")
def serve_output_archive(body: OutputArchiveRequest, request: Request):
    return _serve_output_archive(body.request_ids, request)


@router.get("/output-archive")
def serve_output_archive_query(
    request: Request,
    request_id: list[str] = Query(default=[]),
):
    return _serve_output_archive(request_id, request)


def _serve_output_archive(request_ids: list[str], request: Request):
    if len(request_ids) < 1 or len(request_ids) > 200:
        raise HTTPException(status_code=400, detail="请选择 1 到 200 个任务。")

    config = request.app.state.config
    request_ids = list(dict.fromkeys(request_ids))
    entries: list[tuple[Path, str]] = []
    invalid_ids: list[str] = []
    archive_names: set[str] = set()

    for request_id in request_ids:
        task = get_task(config, request_id)
        if task is None or task.status != "completed" or task.output_path is None:
            invalid_ids.append(request_id)
            continue

        resolved = _safe_resolve(config.output_dir, str(task.output_path))
        if resolved is None or not resolved.is_file():
            invalid_ids.append(request_id)
            continue

        entries.append((resolved, _unique_archive_name(resolved.name, archive_names)))

    if invalid_ids:
        raise HTTPException(
            status_code=400,
            detail=f"这些任务没有可下载结果：{', '.join(invalid_ids[:5])}",
        )
    if not entries:
        raise HTTPException(status_code=400, detail="没有可下载结果。")

    archive_path = _create_output_archive(config.output_dir.parent, entries)
    return FileResponse(
        archive_path,
        media_type="application/zip",
        filename=f"pixloom-results-{strftime('%Y%m%d-%H%M%S')}.zip",
        background=BackgroundTask(_unlink_file, archive_path),
    )


@router.get("/input/{path:path}")
def serve_input(path: str, request: Request):
    config = request.app.state.config
    resolved = _safe_resolve(config.input_dir, path)
    if resolved is None or not resolved.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(resolved)


def _unique_archive_name(name: str, used: set[str]) -> str:
    if name not in used:
        used.add(name)
        return name

    path = Path(name)
    stem = path.stem
    suffix = path.suffix
    index = 2
    while True:
        candidate = f"{stem}-{index}{suffix}"
        if candidate not in used:
            used.add(candidate)
            return candidate
        index += 1


def _create_output_archive(
    temp_root: Path,
    entries: list[tuple[Path, str]],
) -> Path:
    temp_root.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        prefix="pixloom-results-",
        suffix=".zip",
        dir=temp_root,
        delete=False,
    ) as handle:
        archive_path = Path(handle.name)

    try:
        with zipfile.ZipFile(
            archive_path,
            mode="w",
            compression=zipfile.ZIP_STORED,
            allowZip64=True,
        ) as archive:
            for path, archive_name in entries:
                archive.write(path, arcname=archive_name)
    except Exception:
        _unlink_file(archive_path)
        raise

    return archive_path


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


def _unlink_file(path: Path) -> None:
    path.unlink(missing_ok=True)


def _safe_resolve(root: Path, subpath: str) -> Path | None:
    candidate = (root / subpath).resolve()
    root_resolved = root.resolve()
    try:
        candidate.relative_to(root_resolved)
    except ValueError:
        return None
    return candidate
