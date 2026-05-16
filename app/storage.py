from __future__ import annotations

import hashlib
import shutil
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.config import AppConfig


ARCHIVE_PATTERN = "pixloom-results-*.zip"
DEFAULT_THUMBNAIL_CACHE_SIZES = (160, 192)


@dataclass(frozen=True)
class StorageCategory:
    key: str
    label_zh: str
    description_zh: str
    path: Path
    bytes: int
    file_count: int
    percent_of_managed: float


@dataclass(frozen=True)
class DiskUsage:
    total_bytes: int
    used_bytes: int
    free_bytes: int
    used_percent: float


@dataclass(frozen=True)
class StorageRetention:
    enabled: bool
    days: int
    archive_ttl_hours: int
    message_zh: str


@dataclass(frozen=True)
class StorageCleanupResult:
    deleted_paths: tuple[Path, ...] = ()
    bytes_deleted: int = 0


@dataclass(frozen=True)
class StorageSnapshot:
    generated_at: datetime
    total_managed_bytes: int
    disk: DiskUsage
    retention: StorageRetention
    categories: tuple[StorageCategory, ...]


def collect_storage_snapshot(config: AppConfig) -> StorageSnapshot:
    raw_categories = (
        (
            "models",
            "模型文件",
            "推理模型和随镜像同步的本地模型。",
            config.models_dir,
            _scan_directory(config.models_dir),
        ),
        (
            "input",
            "上传原图",
            "浏览器上传后进入队列前保存的原始图片。",
            config.input_dir,
            _scan_directory(config.input_dir),
        ),
        (
            "output",
            "放大结果",
            "已完成任务生成的可下载图片。",
            config.output_dir,
            _scan_directory(config.output_dir),
        ),
        (
            "thumbnails",
            "缩略图缓存",
            "任务列表预览用的 WebP 缓存。",
            config.thumbnail_dir,
            _scan_directory(config.thumbnail_dir),
        ),
        (
            "logs",
            "请求日志",
            "按 request_id 追踪的 JSONL 审计日志。",
            config.logs_dir,
            _scan_directory(config.logs_dir),
        ),
        (
            "state",
            "状态数据库",
            "SQLite 队列、任务状态和临时 WAL 文件。",
            config.db_path.parent,
            _scan_directory(config.db_path.parent),
        ),
        (
            "archives",
            "临时下载包",
            "批量下载时生成并自动回收的 zip 文件。",
            config.output_dir.parent,
            _scan_archives(config),
        ),
    )
    total = sum(
        size for _key, _label, _description, _path, (size, _count) in raw_categories
    )
    categories = tuple(
        StorageCategory(
            key=key,
            label_zh=label,
            description_zh=description,
            path=path,
            bytes=size,
            file_count=count,
            percent_of_managed=round((size / total * 100), 1) if total > 0 else 0.0,
        )
        for key, label, description, path, (size, count) in raw_categories
    )

    disk_root = _disk_root(config)
    disk = shutil.disk_usage(disk_root)
    used = disk.total - disk.free
    retention = StorageRetention(
        enabled=config.history_retention_days > 0,
        days=config.history_retention_days,
        archive_ttl_hours=config.archive_ttl_hours,
        message_zh=_retention_message(config),
    )
    return StorageSnapshot(
        generated_at=datetime.now(timezone.utc),
        total_managed_bytes=total,
        disk=DiskUsage(
            total_bytes=disk.total,
            used_bytes=used,
            free_bytes=disk.free,
            used_percent=round((used / disk.total * 100), 1) if disk.total > 0 else 0.0,
        ),
        retention=retention,
        categories=categories,
    )


def thumbnail_cache_path(config: AppConfig, source: Path, size: int) -> Path:
    stat = source.stat()
    root_resolved = config.output_dir.resolve()
    relative = source.resolve().relative_to(root_resolved).as_posix()
    key = hashlib.sha256(
        f"{relative}:{stat.st_size}:{stat.st_mtime_ns}:{size}".encode("utf-8")
    ).hexdigest()
    return config.thumbnail_dir / f"{key}.webp"


def delete_output_thumbnails(
    config: AppConfig,
    source: Path,
    *,
    sizes: tuple[int, ...] = DEFAULT_THUMBNAIL_CACHE_SIZES,
) -> tuple[Path, ...]:
    deleted: list[Path] = []
    for size in sizes:
        try:
            cache_path = thumbnail_cache_path(config, source, size)
        except (FileNotFoundError, OSError, ValueError):
            continue
        if _unlink_with_result(cache_path):
            deleted.append(cache_path)
    return tuple(deleted)


def cleanup_stale_archives(
    config: AppConfig,
    *,
    older_than_hours: int | None = None,
    now: float | None = None,
) -> StorageCleanupResult:
    ttl_hours = older_than_hours if older_than_hours is not None else config.archive_ttl_hours
    cutoff = (now if now is not None else time.time()) - (ttl_hours * 60 * 60)
    deleted: list[Path] = []
    bytes_deleted = 0
    for path in _archive_paths(config):
        try:
            stat = path.stat()
        except OSError:
            continue
        if stat.st_mtime > cutoff:
            continue
        if _unlink_with_result(path):
            deleted.append(path)
            bytes_deleted += stat.st_size
    return StorageCleanupResult(
        deleted_paths=tuple(deleted),
        bytes_deleted=bytes_deleted,
    )


def cleanup_stale_thumbnails(
    config: AppConfig,
    *,
    older_than_days: int | None = None,
    now: float | None = None,
) -> StorageCleanupResult:
    days = older_than_days if older_than_days is not None else config.history_retention_days
    if days <= 0:
        return StorageCleanupResult()

    cutoff = (now if now is not None else time.time()) - (days * 24 * 60 * 60)
    deleted: list[Path] = []
    bytes_deleted = 0
    if not config.thumbnail_dir.exists():
        return StorageCleanupResult()

    for path in config.thumbnail_dir.rglob("*.webp"):
        try:
            stat = path.stat()
        except OSError:
            continue
        if not path.is_file() or stat.st_mtime > cutoff:
            continue
        if _unlink_with_result(path):
            deleted.append(path)
            bytes_deleted += stat.st_size
    return StorageCleanupResult(
        deleted_paths=tuple(deleted),
        bytes_deleted=bytes_deleted,
    )


def _retention_message(config: AppConfig) -> str:
    archive_text = f"临时下载包保留 {config.archive_ttl_hours} 小时"
    if config.history_retention_days <= 0:
        return f"任务文件自动清理关闭；{archive_text}。"
    return f"任务文件保留最近 {config.history_retention_days} 天；{archive_text}。"


def _disk_root(config: AppConfig) -> Path:
    for path in (
        config.output_dir.parent,
        config.output_dir,
        config.input_dir,
        config.models_dir,
        config.db_path.parent,
    ):
        if path.exists():
            return path
    return Path(".")


def _scan_directory(root: Path) -> tuple[int, int]:
    if not root.exists():
        return 0, 0

    total = 0
    count = 0
    for path in root.rglob("*"):
        try:
            stat = path.stat()
        except OSError:
            continue
        if not path.is_file():
            continue
        total += stat.st_size
        count += 1
    return total, count


def _scan_archives(config: AppConfig) -> tuple[int, int]:
    total = 0
    count = 0
    for path in _archive_paths(config):
        try:
            stat = path.stat()
        except OSError:
            continue
        if not path.is_file():
            continue
        total += stat.st_size
        count += 1
    return total, count


def _archive_paths(config: AppConfig) -> tuple[Path, ...]:
    root = config.output_dir.parent
    if not root.exists():
        return ()
    return tuple(path for path in root.glob(ARCHIVE_PATTERN) if path.is_file())


def _unlink_with_result(path: Path) -> bool:
    try:
        path.unlink()
    except FileNotFoundError:
        return False
    return True
