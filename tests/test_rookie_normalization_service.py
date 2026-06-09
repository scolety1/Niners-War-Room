from __future__ import annotations

from pathlib import Path

import pytest

from src.services.rookie_normalization_service import (
    NormalizationRule,
    draft_pick_curve,
    load_normalization_rules,
    normalize_raw_value,
    normalize_rookie_raw_metrics,
    validate_normalization_rules,
    write_normalized_rookie_inputs,
)

SAMPLE_DIR = Path("sample_data/rookie_model_v1")


def test_draft_pick_curve_is_monotonic_and_bounded() -> None:
    picks = [1, 2, 12, 32, 33, 64, 100, 101, 180, 260]
    scores = [draft_pick_curve(pick) for pick in picks]

    assert scores[0] == 100
    assert scores[-1] == 5
    assert all(0 <= score <= 100 for score in scores)
    assert scores == sorted(scores, reverse=True)


def test_linear_normalization_directions_are_monotonic() -> None:
    higher = NormalizationRule(
        "test_high",
        position="WR",
        feature_name="target_earning",
        raw_metric="target_share",
        transform_type="linear",
        direction="higher_better",
        min_raw=0.10,
        max_raw=0.35,
        missing_policy="missing",
        source_snapshot_id="test",
        notes="",
    )
    lower = NormalizationRule(
        "test_low",
        position="QB",
        feature_name="sack_avoidance",
        raw_metric="pressure_to_sack_rate",
        transform_type="linear",
        direction="lower_better",
        min_raw=0.08,
        max_raw=0.32,
        missing_policy="missing",
        source_snapshot_id="test",
        notes="",
    )

    assert normalize_raw_value(higher, 0.10) == 0
    assert normalize_raw_value(higher, 0.35) == 100
    assert normalize_raw_value(higher, 0.225) == pytest.approx(50, abs=0.1)
    assert normalize_raw_value(lower, 0.08) == 100
    assert normalize_raw_value(lower, 0.32) == 0
    assert normalize_raw_value(lower, 0.20) == pytest.approx(50, abs=0.1)


def test_sample_normalization_rules_are_valid() -> None:
    rules = load_normalization_rules(SAMPLE_DIR / "rookie_normalization_rules.csv")

    validate_normalization_rules(rules)
    assert len(rules) == 22


def test_normalize_raw_metrics_generates_normalized_source_rows(tmp_path) -> None:
    result = normalize_rookie_raw_metrics(
        SAMPLE_DIR / "rookie_raw_metrics.csv",
        SAMPLE_DIR / "rookie_normalization_rules.csv",
    )

    rows = {row["player_id"]: row for row in result.rows}
    assert len(rows) == 5
    assert rows["raw_qb_dual"]["draft_capital"] == 99.3
    assert rows["raw_qb_dual"]["rushing_profile"] == 90.0
    assert rows["raw_qb_dual"]["sack_avoidance"] == 75.0
    assert rows["raw_wr_alpha"]["target_earning"] == 84.0
    assert rows["raw_te_premium"]["route_role"] == 86.0
    assert rows["raw_te_premium"]["athletic_size"] == 72.5

    output = tmp_path / "rookie_prospect_inputs.csv"
    write_normalized_rookie_inputs(output, result.rows)
    assert output.exists()


def test_invalid_normalization_rule_is_rejected() -> None:
    bad_rule = NormalizationRule(
        "bad",
        position="WR",
        feature_name="target_earning",
        raw_metric="target_share",
        transform_type="linear",
        direction="higher_better",
        min_raw=0.35,
        max_raw=0.10,
        missing_policy="missing",
        source_snapshot_id="test",
        notes="",
    )

    with pytest.raises(ValueError, match="min_raw must be below max_raw"):
        validate_normalization_rules((bad_rule,))
