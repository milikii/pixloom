"""GET /api/storage — managed disk usage and cleanup status."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends

from app.config import AppConfig
from app.storage import (
    cleanup_stale_archives,
    cleanup_stale_thumbnails,
    collect_storage_snapshot,
)
from backend.pixloom_api.deps import get_config

router = APIRouter(prefix="/storage", tags=["storage"])


@router.get("")
def get_storage(config: AppConfig = Depends(get_config)):
    archive_cleanup = cleanup_stale_archives(config)
    thumbnail_cleanup = cleanup_stale_thumbnails(config)
    snapshot = collect_storage_snapshot(config)

    return {
        "generated_at": snapshot.generated_at.isoformat(),
        "total_managed_bytes": snapshot.total_managed_bytes,
        "disk": asdict(snapshot.disk),
        "retention": asdict(snapshot.retention),
        "categories": [
            {
                **asdict(category),
                "path": str(category.path),
            }
            for category in snapshot.categories
        ],
        "cleanup": {
            "stale_archives_deleted": len(archive_cleanup.deleted_paths),
            "stale_archive_bytes_deleted": archive_cleanup.bytes_deleted,
            "stale_thumbnails_deleted": len(thumbnail_cleanup.deleted_paths),
            "stale_thumbnail_bytes_deleted": thumbnail_cleanup.bytes_deleted,
        },
    }
