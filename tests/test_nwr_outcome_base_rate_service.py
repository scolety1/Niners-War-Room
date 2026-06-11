from __future__ import annotations

from pathlib import Path

import pytest

from src.services.nwr_outcome_base_rate_service import (
    COMPONENT_WAIVER_ID,
    SCOPE,
    build_limited_truth_set_base_rates,
    export_base_rate_build,
)


def test_base_rate_denominator_excludes_censored_next_year_labels() -> None:
    result = build_limited_truth_set_base_rates(_week_rows())

    row = next(
        bucket
        for bucket in result.bucket_results
        if bucket.position == "WR"
        and bucket.row_family == "all_player_pre_week1"
        and bucket.bucket_family == "position"
        and bucket.outcome_label == "next_year_starter"
    )

    assert row.n_raw == 4
    assert row.raw_rate is not None
    assert row.component_waiver_id == COMPONENT_WAIVER_ID
    assert row.scope == SCOPE
    censoring = next(
        row for row in result.censoring_report if row["outcome_label"] == "next_year_starter"
    )
    assert censoring["censored_or_null_rows"] > 0
    assert censoring["denominator_policy"] == "exclude_null_or_censored_labels"


def test_base_rates_emit_smoothed_posterior_not_just_raw_rate() -> None:
    result = build_limited_truth_set_base_rates(_week_rows())
    row = next(
        bucket
        for bucket in result.bucket_results
        if bucket.position == "WR"
        and bucket.row_family == "all_player_pre_week1"
        and bucket.bucket_family == "prior_finish_tier"
        and bucket.primary_bucket == "prior_difference_maker"
        and bucket.outcome_label == "same_year_starter"
    )

    assert row.raw_rate in {0.0, 1.0}
    assert row.posterior_mean != row.raw_rate
    assert row.parent_rate >= 0
    assert row.prior_alpha > 0
    assert row.prior_beta > 0
    assert row.reliability_flag in {"D", "UNPUBLISHABLE"}


def test_component_waiver_and_scope_are_on_every_output_row() -> None:
    result = build_limited_truth_set_base_rates(_week_rows())

    assert result.bucket_results
    assert all(row.component_waiver_id == COMPONENT_WAIVER_ID for row in result.bucket_results)
    assert all(row.scope == SCOPE for row in result.bucket_results)
    output_groups = (
        result.parent_priors,
        result.input_manifest,
        result.censoring_report,
        result.reliability_report,
        result.leakage_guardrail_report,
    )
    for rows in output_groups:
        assert rows
        assert all(row["component_waiver_id"] == COMPONENT_WAIVER_ID for row in rows)
        assert all(row["scope"] == SCOPE for row in rows)


def test_forbidden_fields_and_imported_fantasy_totals_are_rejected() -> None:
    rows = _week_rows()
    rows[0]["fantasy_points"] = 99

    with pytest.raises(ValueError, match="Forbidden fields"):
        build_limited_truth_set_base_rates(rows)


def test_rookie_post_draft_is_not_included_yet() -> None:
    with pytest.raises(ValueError, match="Unsupported Sprint 4 row family"):
        build_limited_truth_set_base_rates(_week_rows(), row_families=("rookie_post_draft",))


def test_exports_are_local_internal_files(tmp_path: Path) -> None:
    result = build_limited_truth_set_base_rates(_week_rows())
    output_dir = tmp_path / "sprint_4_v0_base_rates"

    paths = export_base_rate_build(result, output_dir)

    assert {path.name for path in paths} == {
        "base_rate_bucket_results.csv",
        "base_rate_parent_priors.csv",
        "base_rate_input_manifest.csv",
        "base_rate_censoring_report.csv",
        "base_rate_reliability_report.csv",
        "base_rate_leakage_guardrail_report.csv",
    }
    assert all(path.exists() for path in paths)


def _week_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    players = [
        ("wr_alpha", "Alpha WR", "WR", 20),
        ("wr_beta", "Beta WR", "WR", 8),
        ("rb_alpha", "Alpha RB", "RB", 18),
        ("rb_beta", "Beta RB", "RB", 7),
    ]
    for season in (2022, 2023, 2024):
        for player_id, player_name, position, base_score in players:
            rows.append(
                {
                    "truth_set_player_name": player_name,
                    "matched_player_name": player_name,
                    "match_status": "matched",
                    "player_id": player_id,
                    "season": season,
                    "week": 1,
                    "team": "SF",
                    "position": position,
                    "passing_yards": 0,
                    "passing_tds": 0,
                    "interceptions": 0,
                    "rushing_attempts": 0,
                    "rushing_yards": base_score * 10 if position == "RB" else 0,
                    "rushing_tds": 0,
                    "targets": 0,
                    "receptions": 0,
                    "receiving_yards": base_score * 10 if position == "WR" else 0,
                    "receiving_tds": 0,
                    "rushing_first_downs": 0,
                    "receiving_first_downs": 0,
                    "total_fumbles": 0,
                    "fumbles_lost": 0,
                    "source_status": "source_safe",
                    "source_name": "truth_set_v3",
                    "source_url": "local",
                    "source_date": "2026-05-15",
                    "notes": "",
                }
            )
    return rows
