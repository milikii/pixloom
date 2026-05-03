from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from app.model_registry import ExposureLevel, ModelDefinition, get_default_registry


@dataclass(frozen=True)
class ModelInventoryEntry:
    file_name: str
    size_bytes: int
    sha256: str
    registry_id: str
    display_name_zh: str
    enabled: bool
    exposure: ExposureLevel | str
    operator_visible: bool
    stability_zh: str


def build_model_inventory(
    models_dir: Path,
    registry: tuple[ModelDefinition, ...] | None = None,
) -> list[ModelInventoryEntry]:
    definitions = registry if registry is not None else get_default_registry()
    by_name = {definition.path.name: definition for definition in definitions}
    entries: list[ModelInventoryEntry] = []

    for path in sorted(models_dir.glob("*")):
        if not path.is_file():
            continue
        if path.name.startswith("."):
            continue
        definition = by_name.get(path.name)
        sha256 = _sha256(path)

        if definition is None:
            entries.append(
                ModelInventoryEntry(
                    file_name=path.name,
                    size_bytes=path.stat().st_size,
                    sha256=sha256,
                    registry_id="",
                    display_name_zh="",
                    enabled=False,
                    exposure="untracked",
                    operator_visible=False,
                    stability_zh="未登记",
                )
            )
            continue

        entries.append(
            ModelInventoryEntry(
                file_name=path.name,
                size_bytes=path.stat().st_size,
                sha256=sha256,
                registry_id=definition.id,
                display_name_zh=definition.display_name_zh,
                enabled=definition.enabled,
                exposure=definition.exposure,
                operator_visible=definition.enabled and definition.exposure == "operator",
                stability_zh=definition.stability_zh,
            )
        )

    return entries


def format_inventory_markdown(entries: list[ModelInventoryEntry]) -> str:
    lines = [
        "| File | Size | SHA256 | Registry id | Exposure | Visible in dropdown | Stability |",
        "|---|---:|---|---|---|---|---|",
    ]
    for entry in entries:
        lines.append(
            "| "
            f"`{entry.file_name}` | "
            f"`{entry.size_bytes}` bytes | "
            f"`{entry.sha256}` | "
            f"`{entry.registry_id or '-'}` | "
            f"`{entry.exposure}` | "
            f"`{'yes' if entry.operator_visible else 'no'}` | "
            f"`{entry.stability_zh}` |"
        )
    return "\n".join(lines)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    entries = build_model_inventory(Path("models"))
    print(format_inventory_markdown(entries))


if __name__ == "__main__":
    main()
