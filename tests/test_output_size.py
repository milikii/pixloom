from __future__ import annotations

import pytest

from app.output_size import (
    build_output_size_plan,
    normalize_output_size_preset,
    output_size_label_zh,
    resize_to_longest_side,
)


def test_normalize_output_size_preset_defaults_to_native():
    assert normalize_output_size_preset(None) == "native"
    assert normalize_output_size_preset("") == "native"
    assert normalize_output_size_preset("4K") == "4k"


def test_normalize_output_size_preset_rejects_unknown_value():
    with pytest.raises(ValueError, match="output_size_preset"):
        normalize_output_size_preset("16k")


def test_resize_to_longest_side_preserves_aspect_ratio():
    assert resize_to_longest_side((1000, 500), 2048) == (2048, 1024)
    assert resize_to_longest_side((500, 1000), 2048) == (1024, 2048)
    assert resize_to_longest_side((1000, 1000), 2048) == (2048, 2048)


def test_build_output_size_plan_native_uses_model_scale():
    plan = build_output_size_plan(
        input_size=(800, 600),
        model_scale=4,
        preset="native",
    )

    assert plan.preset == "native"
    assert plan.prepared_input_size == (800, 600)
    assert plan.expected_output_size == (3200, 2400)
    assert plan.final_output_size == (3200, 2400)
    assert not plan.requires_pre_resize
    assert not plan.requires_final_resize


def test_build_output_size_plan_targets_final_longest_side():
    plan = build_output_size_plan(
        input_size=(800, 600),
        model_scale=4,
        preset="2k",
    )

    assert plan.target_longest_side == 2048
    assert plan.prepared_input_size == (512, 384)
    assert plan.expected_output_size == (2048, 1536)
    assert plan.final_output_size == (2048, 1536)


def test_build_output_size_plan_handles_scale_mismatch_with_final_resize():
    plan = build_output_size_plan(
        input_size=(801, 600),
        model_scale=3,
        preset="2k",
    )

    assert max(plan.final_output_size) == 2048
    assert max(plan.expected_output_size) <= 2048
    assert plan.requires_final_resize


def test_build_output_size_plan_caps_prepared_input_side_when_configured():
    plan = build_output_size_plan(
        input_size=(1200, 800),
        model_scale=1,
        preset="8k",
        max_prepared_input_side=2048,
    )

    assert plan.prepared_input_size == (2048, 1365)
    assert plan.expected_output_size == (2048, 1365)
    assert plan.final_output_size == (8192, 5461)
    assert plan.requires_final_resize


def test_output_size_label_zh_is_operator_readable():
    assert output_size_label_zh("native") == "原始模型倍率"
    assert output_size_label_zh("8k") == "8K 最长边 8192px"
