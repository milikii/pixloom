"""POST /api/upload — upload image files to input/."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile

from app.config import AppConfig
from app.inference import persist_upload, validate_upload, InferenceError
from backend.pixloom_api.deps import get_config

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("")
async def upload_files(
    files: list[UploadFile], config: AppConfig = Depends(get_config)
):
    uploaded: list[dict[str, object]] = []

    for f in files:
        if not f.filename:
            continue
        tmp = Path(f"/tmp/{f.filename}")
        try:
            content = await f.read()
            tmp.write_bytes(content)

            validate_upload(tmp, config)
            stored = persist_upload(tmp, config, original_name=f.filename)

            uploaded.append(
                {
                    "original_name": f.filename,
                    "stored_path": str(stored),
                    "size_bytes": stored.stat().st_size,
                }
            )
        finally:
            if tmp.exists():
                tmp.unlink(missing_ok=True)

    return {"uploaded": uploaded}
