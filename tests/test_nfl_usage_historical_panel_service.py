from __future__ import annotations

import pandas as pd

from src.services.nfl_usage_historical_panel_service import (
    VALID_READINESS_STATUSES,
    build_historical_usage_panel,
    build_panels,
    derived_dictionary_rows,
    field_coverage_rows,
    validate_csv_flags,
)


def _sample_frames() -> dict[str, pd.DataFrame]:
    player_rows = []
    snap_rows = []
    pbp_rows = []
    for season in (2022, 2023, 2024):
        for week in (1, 2):
            player_rows.append(
                {
                    "season": season,
                    "week": week,
                    "player_id": "00-0001",
                    "player_display_name": "Example Back",
                    "position": "RB",
                    "team": "SF",
                    "targets": 2,
                    "carries": 10,
                    "receptions": 1,
                    "rushing_yards": 50,
                    "receiving_yards": 8,
                    "receiving_air_yards": 5,
                    "receiving_yards_after_catch": 6,
                    "rushing_first_downs": 3,
                    "receiving_first_downs": 1,
                }
            )
            snap_rows.append(
                {
                    "season": season,
                    "week": week,
                    "player": "Example Back",
                    "position": "RB",
                    "team": "SF",
                    "offense_snaps": 42,
                    "offense_pct": 0.67,
                }
            )
            pbp_rows.extend(
                [
                    {
                        "season": season,
                        "week": week,
                        "posteam": "SF",
                        "yardline_100": 8,
                        "rush_attempt": 1,
                        "rusher_player_id": "00-0001",
                        "rusher_player_name": "Example Back",
                    },
                    {
                        "season": season,
                        "week": week,
                        "posteam": "SF",
                        "yardline_100": 4,
                        "pass_attempt": 1,
                        "complete_pass": 1,
                        "receiver_player_id": "00-0001",
                        "receiver_player_name": "Example Back",
                    },
                ]
            )
    return {
        "player_stats": pd.DataFrame(player_rows),
        "snap_counts": pd.DataFrame(snap_rows),
        "pbp": pd.DataFrame(pbp_rows),
    }


def test_historical_panel_builds_manifests_and_flags(tmp_path) -> None:
    result = build_historical_usage_panel(
        frames=_sample_frames(),
        doc_root=tmp_path / "docs",
        shared_cache_root=tmp_path / "shared",
        write=True,
    )

    assert result.files_written
    validate_csv_flags(list(result.files_written))
    manifest = pd.read_csv(
        tmp_path / "docs" / "historical_usage_panel_manifest_v0.csv",
        keep_default_na=False,
    )
    assert set(manifest["committed_to_git"]) == {"no"}
    assert set(manifest["raw_payload_included"]) == {"no"}
    assert set(manifest["model_input_allowed"]) == {"no"}
    assert set(manifest["app_wiring_allowed"]) == {"no"}


def test_field_coverage_matrix_loads_and_has_valid_statuses() -> None:
    panels = build_panels(_sample_frames())
    rows = field_coverage_rows(panels, [2022, 2023, 2024])
    by_field = {row["field_name"]: row for row in rows}

    assert by_field["targets"]["coverage_status"] == "GREEN_MULTI_SEASON_COVERAGE"
    assert by_field["offense_snaps"]["coverage_status"] == "YELLOW_COVERAGE_ID_JOIN_CAVEAT"
    assert by_field["true_routes_run"]["coverage_status"] == "BLOCKED_LICENSED_DATA_GAP"


def test_validation_and_quarantine_reports_load(tmp_path) -> None:
    build_historical_usage_panel(
        frames=_sample_frames(),
        doc_root=tmp_path,
        shared_cache_root=tmp_path / "shared",
        write=True,
    )

    validation = pd.read_csv(tmp_path / "historical_usage_validation_report_v0.csv")
    quarantine = pd.read_csv(tmp_path / "historical_usage_quarantine_report_v0.csv")
    assert not validation.empty
    assert not quarantine.empty


def test_derived_formulas_are_labeled() -> None:
    rows = derived_dictionary_rows()
    assert rows
    assert all(row["derivation_formula"] for row in rows)
    assert {row["model_input_allowed"] for row in rows} == {"no"}
    assert {row["app_wiring_allowed"] for row in rows} == {"no"}


def test_backtest_readiness_statuses_are_valid(tmp_path) -> None:
    build_historical_usage_panel(
        frames=_sample_frames(),
        doc_root=tmp_path,
        shared_cache_root=tmp_path / "shared",
        write=True,
    )

    readiness = pd.read_csv(tmp_path / "historical_usage_backtest_readiness_matrix_v0.csv")
    assert set(readiness["recommended_backtest_status"]).issubset(VALID_READINESS_STATUSES)


def test_no_app_decision_or_rank_files_are_required() -> None:
    panels = build_panels(_sample_frames())
    assert "player_week_core_usage_panel" in panels
    assert all("model_input_allowed" in panel for panel in panels.values())
    assert all("app_wiring_allowed" in panel for panel in panels.values())
