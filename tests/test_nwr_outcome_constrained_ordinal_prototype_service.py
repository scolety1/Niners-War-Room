from __future__ import annotations

from src.services.nwr_outcome_constrained_ordinal_prototype_service import (
    APP_RELEASE_STATUS,
    OUTPUT_SCOPE,
    all_rows_are_quarantined,
    artifact_quarantine_rows,
    compare_internal_threshold_methods,
    forward_clamp_non_decreasing,
    pava_non_decreasing,
)


def test_pava_projection_enforces_non_decreasing_chain_with_smaller_max_delta() -> None:
    raw = (0.012348, 0.009454, 0.007229, 0.011547, 0.020901)

    clamped = forward_clamp_non_decreasing(raw)
    constrained = pava_non_decreasing(raw)

    assert all(
        left <= right
        for left, right in zip(constrained[:-1], constrained[1:], strict=True)
    )
    assert all(left <= right for left, right in zip(clamped[:-1], clamped[1:], strict=True))
    assert max(abs(new - old) for old, new in zip(raw, constrained, strict=True)) < max(
        abs(new - old) for old, new in zip(raw, clamped, strict=True)
    )


def test_comparison_reports_raw_violations_and_repaired_zero_violations() -> None:
    rows = _rb_prediction_rows(
        {
            "same_year_rb_t6": 0.04,
            "same_year_rb_t12": 0.08,
            "same_year_rb_t24": 0.12,
            "same_year_rb_t36": 0.23,
            "same_year_rb_t48": 0.22,
        }
    )

    result = compare_internal_threshold_methods(rows)

    assert len(result["raw_violations"]) == 1
    assert result["raw_violations"][0]["violating_pair_label"] == "T36>T48"
    assert result["clamped_violations"] == []
    assert result["constrained_violations"] == []
    assert result["summary_rows"][0]["exact_percentage_display_allowed"] == "no"
    assert result["summary_rows"][0]["ranking_use_allowed"] == "no"


def test_row_level_outputs_are_quarantined_not_app_readable_or_sortable() -> None:
    rows = _rb_prediction_rows(
        {
            "same_year_rb_t6": 0.04,
            "same_year_rb_t12": 0.08,
            "same_year_rb_t24": 0.12,
            "same_year_rb_t36": 0.23,
            "same_year_rb_t48": 0.22,
        }
    )

    result = compare_internal_threshold_methods(rows)
    row_level = (
        result["raw_violations"]
        + result["clamped_adjustments"]
        + result["constrained_adjustments"]
    )

    assert row_level
    assert all_rows_are_quarantined(row_level)
    assert {row["app_release_status"] for row in row_level} == {APP_RELEASE_STATUS}
    assert {row["output_scope"] for row in row_level} == {OUTPUT_SCOPE}


def test_artifact_quarantine_allows_only_local_exports_scope() -> None:
    rows = artifact_quarantine_rows(
        "C:/repo/local_exports/outcome_probability/"
        "sprint_5bf_constrained_ordinal_internal_prototype"
    )

    assert rows[0]["gate"] == "output_folder_scope"
    assert rows[0]["status"] == "pass"
    assert all(row["release_impact"] != "released" for row in rows)


def _rb_prediction_rows(probabilities: dict[str, float]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for target, value in probabilities.items():
        rows.append(
            {
                "output_scope": "internal_only_not_released",
                "app_release_status": "blocked_not_app_readable",
                "sort_allowed": "no",
                "ranking_use_allowed": "no",
                "row_id": "row_1",
                "current_player_id": "p1",
                "player_name": "Internal Back",
                "position": "RB",
                "target": target,
                "threshold": target.rsplit("_", 1)[-1].upper(),
                "model_family": "test_raw_independent",
                "internal_probability_unreleased": str(value),
                "source_feature_status": "ready_feature_snapshot",
                "exact_percentage_display_allowed": "no",
                "coarse_band_display_allowed": "no",
            }
        )
    return rows
