"""GET /api/files/output/{path}, GET /api/files/input/{path} — static file serving."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

router = APIRouter(prefix="/files", tags=["files"])


@router.get("/output/{path:path}")
def serve_output(path: str, request: Request):
    config = request.app.state.config
    resolved = _safe_resolve(config.output_dir, path)
    if resolved is None or not resolved.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(resolved)


@router.get("/input/{path:path}")
def serve_input(path: str, request: Request):
    config = request.app.state.config
    resolved = _safe_resolve(config.input_dir, path)
    if resolved is None or not resolved.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(resolved)


def _safe_resolve(root: Path, subpath: str) -> Path | None:
    candidate = (root / subpath).resolve()
    root_resolved = root.resolve()
    try:
        candidate.relative_to(root_resolved)
    except ValueError:
        return None
    return candidate
