from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


OutputSizePreset = Literal["native", "2k", "4k", "8k"]

NATIVE_OUTPUT_SIZE_PRESET: OutputSizePreset = "native"
OUTPUT_SIZE_TARGETS: dict[OutputSizePreset, int | None] = {
    "native": None,
    "2k": 2048,
    "4k": 4096,
    "8k": 8192,
}
OUTPUT_SIZE_LABELS_ZH: dict[OutputSizePreset, str] = {
    "native": "原始模型倍率",
    "2k": "2K 最长边 2048px",
    "4k": "4K 最长边 4096px",
    "8k": "8K 最长边 8192px",
}


@dataclass(frozen=True)
class OutputSizePlan:
    preset: OutputSizePreset
    label_zh: str
    target_longest_side: int | None
    prepared_input_size: tuple[int, int]
    expected_output_size: tuple[int, int]
    final_output_size: tuple[int, int]
    requires_pre_resize: bool
    requires_final_resize: bool


def normalize_output_size_preset(value: str | None) -> OutputSizePreset:
    normalized = (value or NATIVE_OUTPUT_SIZE_PRESET).strip().lower()
    if normalized not in OUTPUT_SIZE_TARGETS:
        allowed = ", ".join(OUTPUT_SIZE_TARGETS)
        raise ValueError(f"output_size_preset must be one of: {allowed}")
    return normalized  # type: ignore[return-value]


def output_size_label_zh(preset: str | None) -> str:
    return OUTPUT_SIZE_LABELS_ZH[normalize_output_size_preset(preset)]


def build_output_size_plan(
    *,
    input_size: tuple[int, int],
    model_scale: int,
    preset: str | None,
    max_prepared_input_side: int | None = None,
) -> OutputSizePlan:
    resolved = normalize_output_size_preset(preset)
    width, height = input_size
    scale = max(1, int(model_scale))
    native_output_size = (width * scale, height * scale)
    target_longest_side = OUTPUT_SIZE_TARGETS[resolved]

    if target_longest_side is None:
        return OutputSizePlan(
            preset=resolved,
            label_zh=OUTPUT_SIZE_LABELS_ZH[resolved],
            target_longest_side=None,
            prepared_input_size=(width, height),
            expected_output_size=native_output_size,
            final_output_size=native_output_size,
            requires_pre_resize=False,
            requires_final_resize=False,
        )

    final_output_size = resize_to_longest_side(
        (width, height),
        target_longest_side,
    )
    prepared_longest_side = max(1, target_longest_side // scale)
    if max_prepared_input_side is not None:
        prepared_longest_side = min(
            prepared_longest_side,
            max(1, int(max_prepared_input_side)),
        )
    prepared_input_size = resize_to_longest_side(
        (width, height),
        prepared_longest_side,
    )
    expected_output_size = (
        prepared_input_size[0] * scale,
        prepared_input_size[1] * scale,
    )

    return OutputSizePlan(
        preset=resolved,
        label_zh=OUTPUT_SIZE_LABELS_ZH[resolved],
        target_longest_side=target_longest_side,
        prepared_input_size=prepared_input_size,
        expected_output_size=expected_output_size,
        final_output_size=final_output_size,
        requires_pre_resize=prepared_input_size != (width, height),
        requires_final_resize=expected_output_size != final_output_size,
    )


def resize_to_longest_side(
    size: tuple[int, int],
    longest_side: int,
) -> tuple[int, int]:
    width, height = size
    if width <= 0 or height <= 0:
        raise ValueError("image dimensions must be positive")
    if longest_side <= 0:
        raise ValueError("longest_side must be positive")

    if width >= height:
        new_width = longest_side
        new_height = max(1, round(height * longest_side / width))
    else:
        new_height = longest_side
        new_width = max(1, round(width * longest_side / height))
    return (new_width, new_height)
