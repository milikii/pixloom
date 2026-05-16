from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.config import AppConfig
from app.request_logging import log_event
from app.storage import cleanup_stale_thumbnails, delete_output_thumbnails


DELETION_EVENTS = {"history_deleted", "history_pruned", "task_deleted"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


@dataclass(frozen=True)
class HistoryItem:
    request_id: str
    timestamp: datetime
    output_path: Path
    input_path: Path | None
    input_filename: str
    model_id: str
    elapsed_seconds: float | None


@dataclass(frozen=True)
class HistoryDeleteResult:
    request_id: str
    deleted_paths: tuple[Path, ...]
    missing_paths: tuple[Path, ...]
    message_zh: str


@dataclass(frozen=True)
class HistoryCleanupResult:
    deleted_paths: tuple[Path, ...] = ()
    pruned_requests: tuple[str, ...] = ()
    skipped: bool = False


def _parse_timestamp(value: object) -> datetime:
    if not isinstance(value, str) or not value:
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _payloads(config: AppConfig) -> list[dict[str, object]]:
    if not config.logs_dir.exists():
        return []

    rows: list[dict[str, object]] = []
    for path in sorted(config.logs_dir.glob("pixloom-*.jsonl")):
        with path.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                try:
                    payload = json.loads(raw_line)
                except json.JSONDecodeError:
                    continue
                if isinstance(payload, dict):
                    rows.append(payload)
    return rows


def _safe_child(raw_path: object, root: Path) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path:
        return None

    candidate = Path(raw_path)
    root_resolved = root.resolve(strict=False)
    candidate_resolved = candidate.resolve(strict=False)
    try:
        candidate_resolved.relative_to(root_resolved)
    except ValueError:
        return None
    return candidate_resolved


def _history_item_from_payload(
    payload: dict[str, object], config: AppConfig
) -> HistoryItem | None:
    request_id = payload.get("request_id")
    if not isinstance(request_id, str) or not request_id:
        return None

    output_path = _safe_child(payload.get("output_path"), config.output_dir)
    if output_path is None or not output_path.is_file():
        return None

    input_path = _safe_child(payload.get("input_path"), config.input_dir)
    if input_path is not None and not input_path.is_file():
        input_path = None

    input_filename = payload.get("input_filename")
    model_id = payload.get("model_id")
    elapsed_seconds = payload.get("elapsed_seconds")
    return HistoryItem(
        request_id=request_id,
        timestamp=_parse_timestamp(payload.get("timestamp")),
        output_path=output_path,
        input_path=input_path,
        input_filename=input_filename if isinstance(input_filename, str) else "",
        model_id=model_id if isinstance(model_id, str) else "",
        elapsed_seconds=(
            float(elapsed_seconds)
            if isinstance(elapsed_seconds, int | float)
            else None
        ),
    )


def list_history_items(config: AppConfig, limit: int | None = None) -> list[HistoryItem]:
    rows = _payloads(config)
    deleted_request_ids = {
        row.get("request_id")
        for row in rows
        if row.get("event") in DELETION_EVENTS and isinstance(row.get("request_id"), str)
    }

    by_request: dict[str, HistoryItem] = {}
    for row in rows:
        if row.get("event") != "request_succeeded" or row.get("status") != "success":
            continue
        item = _history_item_from_payload(row, config)
        if item is None or item.request_id in deleted_request_ids:
            continue
        current = by_request.get(item.request_id)
        if current is None or item.timestamp >= current.timestamp:
            by_request[item.request_id] = item

    items = sorted(
        by_request.values(), key=lambda item: item.timestamp, reverse=True
    )
    if limit is not None:
        return items[:limit]
    return items


def _unlink_file(path: Path) -> bool:
    try:
        path.unlink()
    except FileNotFoundError:
        return False
    return True


def delete_history_item(config: AppConfig, request_id: str) -> HistoryDeleteResult:
    item = next(
        (candidate for candidate in list_history_items(config) if candidate.request_id == request_id),
        None,
    )
    if item is None:
        return HistoryDeleteResult(
            request_id=request_id,
            deleted_paths=(),
            missing_paths=(),
            message_zh="没有找到可删除的历史任务，可能已经被删除或文件已不存在。",
        )

    deleted_paths: list[Path] = []
    missing_paths: list[Path] = []
    for path in (item.output_path, item.input_path):
        if path is None:
            continue
        if path == item.output_path:
            deleted_paths.extend(delete_output_thumbnails(config, path))
        if _unlink_file(path):
            deleted_paths.append(path)
        else:
            missing_paths.append(path)

    log_event(
        config,
        request_id=item.request_id,
        event="history_deleted",
        status="deleted",
        model_id=item.model_id,
        input_filename=item.input_filename,
        input_path=item.input_path,
        output_path=item.output_path,
    )

    deleted_text = "\n".join(str(path) for path in deleted_paths) or "没有实际删除文件。"
    return HistoryDeleteResult(
        request_id=item.request_id,
        deleted_paths=tuple(deleted_paths),
        missing_paths=tuple(missing_paths),
        message_zh=f"已删除历史任务：{item.request_id}\n删除文件：\n{deleted_text}",
    )


def _delete_runtime_orphans(
    *,
    root: Path,
    cutoff: datetime,
    keep_paths: set[Path],
) -> list[Path]:
    if not root.exists():
        return []

    deleted: list[Path] = []
    for path in root.iterdir():
        if not path.is_file() or path.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        resolved = path.resolve(strict=False)
        if resolved in keep_paths:
            continue
        modified = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        if modified >= cutoff:
            continue
        if _unlink_file(path):
            deleted.append(resolved)
    return deleted


def cleanup_expired_history(config: AppConfig) -> HistoryCleanupResult:
    if config.history_retention_days <= 0:
        return HistoryCleanupResult(skipped=True)

    cutoff = datetime.now(timezone.utc) - timedelta(days=config.history_retention_days)
    task_pruned_paths, task_pruned_requests = _cleanup_expired_task_records(
        config=config,
        cutoff=cutoff,
    )
    items = list_history_items(config)
    expired = [item for item in items if item.timestamp < cutoff]
    kept = [item for item in items if item.timestamp >= cutoff]

    deleted_paths: list[Path] = list(task_pruned_paths)
    pruned_requests: list[str] = list(task_pruned_requests)
    for item in expired:
        removed_for_item = []
        for path in (item.output_path, item.input_path):
            if path == item.output_path:
                deleted_paths.extend(delete_output_thumbnails(config, path))
            if path is not None and _unlink_file(path):
                removed_for_item.append(path)
                deleted_paths.append(path)
        log_event(
            config,
            request_id=item.request_id,
            event="history_pruned",
            status="deleted",
            model_id=item.model_id,
            input_filename=item.input_filename,
            input_path=item.input_path,
            output_path=item.output_path,
        )
        if removed_for_item:
            pruned_requests.append(item.request_id)

    keep_input_paths = {
        item.input_path.resolve(strict=False)
        for item in kept
        if item.input_path is not None
    }
    keep_output_paths = {item.output_path.resolve(strict=False) for item in kept}
    deleted_paths.extend(
        _delete_runtime_orphans(
            root=config.input_dir,
            cutoff=cutoff,
            keep_paths=keep_input_paths,
        )
    )
    deleted_paths.extend(
        _delete_runtime_orphans(
            root=config.output_dir,
            cutoff=cutoff,
            keep_paths=keep_output_paths,
        )
    )
    deleted_paths.extend(cleanup_stale_thumbnails(config).deleted_paths)

    return HistoryCleanupResult(
        deleted_paths=tuple(deleted_paths),
        pruned_requests=tuple(pruned_requests),
        skipped=False,
    )


def _cleanup_expired_task_records(
    *,
    config: AppConfig,
    cutoff: datetime,
) -> tuple[tuple[Path, ...], tuple[str, ...]]:
    from app.tasks import delete_task, list_tasks

    deleted_paths: list[Path] = []
    pruned_requests: list[str] = []
    for task in list_tasks(config, limit=None):
        if task.status in {"queued", "running", "deleted"}:
            continue
        task_time = task.completed_at or task.started_at or task.created_at
        if task_time >= cutoff:
            continue
        result = delete_task(config, task.request_id)
        deleted_paths.extend(result.deleted_paths)
        if result.deleted_paths or result.missing_paths:
            pruned_requests.append(task.request_id)
    return tuple(deleted_paths), tuple(pruned_requests)
