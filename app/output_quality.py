from __future__ import annotations


FIXED_OUTPUT_QUALITY = 100


def normalize_output_quality(_: int | None = None) -> int:
    return FIXED_OUTPUT_QUALITY
