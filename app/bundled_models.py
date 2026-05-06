from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from app.config import AppConfig


@dataclass(frozen=True)
class BundledModelSyncResult:
    copied_files: tuple[Path, ...]
    skipped_existing: tuple[Path, ...]


def sync_bundled_models(config: AppConfig) -> BundledModelSyncResult:
    source_root = config.bundled_models_dir
    target_root = config.models_dir

    if not source_root.is_dir():
        return BundledModelSyncResult(copied_files=(), skipped_existing=())

    copied: list[Path] = []
    skipped: list[Path] = []

    for source_path in sorted(source_root.rglob("*")):
        if not source_path.is_file():
            continue
        relative_path = source_path.relative_to(source_root)
        target_path = target_root / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        if target_path.exists():
            skipped.append(target_path)
            continue
        shutil.copy2(source_path, target_path)
        copied.append(target_path)

    return BundledModelSyncResult(
        copied_files=tuple(copied),
        skipped_existing=tuple(skipped),
    )
