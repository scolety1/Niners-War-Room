from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.services.outcome_v2_current_player_display_service import (
    NOT_ENOUGH_INFORMATION,
    build_current_player_display_artifact,
    summarize_current_player_display_artifact,
    write_current_player_display_artifact,
)


def test_artifact_includes_current_board_rows_and_display_probability() -> None:
    artifact = _artifact()
    alpha = artifact[artifact["nwr_player_id"] == "1"].iloc[0]

    assert len(artifact) == 4
    assert alpha["eligibility_status"] == "eligible_veteran_feature_covered"
    assert alpha["QB T6 This Year"] == "50.0%"
    assert alpha["QB T12 This Year"] == "60.0%"
    assert alpha["display_only"] == "true"
    assert alpha["model_use_allowed"] == "false"
    assert alpha["training_allowed"] == "false"
    assert alpha["source_truth_allowed"] == "false"


def test_missing_feature_rows_are_not_enough_information_not_zero() -> None:
    artifact = _artifact()
    beta = artifact[artifact["nwr_player_id"] == "2"].iloc[0]

    assert beta["eligibility_status"] == "missing_current_feature_coverage"
    assert beta["feature_coverage_status"] == "missing_2025_feature_row"
    assert beta["RB T24 Within 5Y"] == NOT_ENOUGH_INFORMATION
    assert "0%" not in set(beta.tolist())
    assert "false" not in {
        beta["RB T24 Within 5Y"],
        beta["RB T36 Within 5Y"],
    }


def test_rookies_and_unsupported_positions_are_out_of_scope() -> None:
    artifact = _artifact()
    rookie = artifact[artifact["nwr_player_id"] == "3"].iloc[0]
    kicker = artifact[artifact["nwr_player_id"] == "4"].iloc[0]

    assert rookie["eligibility_status"] == "out_of_scope_rookie_or_prospect"
    assert rookie["WR T6 This Year"] == NOT_ENOUGH_INFORMATION
    assert kicker["eligibility_status"] == "out_of_scope_unsupported_position"
    assert kicker["QB T6 This Year"] == NOT_ENOUGH_INFORMATION


def test_blocked_rb_five_year_fields_are_not_probability_columns() -> None:
    artifact = _artifact()

    assert "RB T6 Within 5Y" not in artifact.columns
    assert "RB T12 Within 5Y" not in artifact.columns
    assert "RB T24 Within 5Y" in artifact.columns
    assert "RB T36 Within 5Y" in artifact.columns


def test_missing_games_adds_availability_caveat() -> None:
    artifact = _artifact()
    alpha = artifact[artifact["nwr_player_id"] == "1"].iloc[0]

    assert alpha["availability_context_status"] == "partial_availability_context_missing_games"
    assert "games missing" in alpha["caveat_summary"]
    assert alpha["scoring_mode"] == "partial_exact_first_down_scoring_missing_sack_fumbles_lost"


def test_no_blocked_source_columns_are_carried_into_artifact() -> None:
    artifact = _artifact()
    blocked_terms = ("market", "adp", "dynastyprocess", "cfbd", "rank", "score")

    assert not any(
        term in column.lower()
        for column in artifact.columns
        for term in blocked_terms
        if column
        not in {
            "market_used_as_input",
            "adp_used_as_input",
            "dynastyprocess_used_as_input",
            "cfbd_used_as_input",
        }
    )
    assert set(artifact["market_used_as_input"]) == {"false"}
    assert set(artifact["dynastyprocess_used_as_input"]) == {"false"}
    assert set(artifact["adp_used_as_input"]) == {"false"}
    assert set(artifact["cfbd_used_as_input"]) == {"false"}


def test_summary_counts_probability_ready_and_not_enough_rows() -> None:
    artifact = _artifact()
    result = summarize_current_player_display_artifact(artifact, _validation_results())

    assert result.row_count == 4
    assert result.eligible_probability_rows == 1
    assert result.not_enough_information_rows == 3
    assert result.rookie_out_of_scope_rows == 1
    assert result.missing_feature_rows == 1
    assert result.unsupported_position_rows == 1
    assert result.blocked_fields == ("RB_T6_WITHIN_5Y", "RB_T12_WITHIN_5Y")


def test_writer_creates_compact_source_safe_artifact(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    source_root.mkdir()
    stats_path = source_root / "player_season_stats_display_context.csv"
    manifest_path = source_root / "manifest.json"
    pointer_path = tmp_path / "latest_candidate.json"
    board_path = tmp_path / "board.csv"
    bridge_path = tmp_path / "bridge.csv"
    validation_path = tmp_path / "validation.csv"
    buckets_path = tmp_path / "buckets.csv"
    output_path = tmp_path / "out" / "display.csv"

    _current_board().to_csv(board_path, index=False)
    _season_stats().to_csv(stats_path, index=False)
    _identity_bridge().to_csv(bridge_path, index=False)
    _validation_results().to_csv(validation_path, index=False)
    _model_bucket_rates().to_csv(buckets_path, index=False)
    manifest_path.write_text(json.dumps({"data_file": stats_path.name}), encoding="utf-8")
    pointer_path.write_text(
        json.dumps(
            {
                "snapshot_path": str(source_root),
                "data_file": stats_path.name,
                "manifest_path": str(manifest_path),
            }
        ),
        encoding="utf-8",
    )

    result = write_current_player_display_artifact(
        output_path=output_path,
        current_board_path=board_path,
        season_stats_pointer_path=pointer_path,
        identity_bridge_path=bridge_path,
        validation_results_path=validation_path,
        model_bucket_rates_path=buckets_path,
    )
    written = pd.read_csv(result.artifact_path, dtype=str).fillna("")

    assert result.row_count == 4
    assert output_path.exists()
    assert "passing_yards" not in written.columns
    assert "nwr_dynasty_score" not in written.columns
    assert "market_rank" not in written.columns
    assert result.sha256


def _artifact() -> pd.DataFrame:
    return build_current_player_display_artifact(
        _current_board(),
        _season_stats(),
        _identity_bridge(),
        _validation_results(),
        _model_bucket_rates(),
    )


def _current_board() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "player_id": "1",
                "player_name": "Alpha QB",
                "position": "QB",
                "nfl_team": "SF",
                "market_rank": "1",
                "nwr_dynasty_score": "99",
            },
            {
                "player_id": "2",
                "player_name": "Beta RB",
                "position": "RB",
                "nfl_team": "SEA",
            },
            {
                "player_id": "3",
                "player_name": "Rookie WR",
                "position": "WR",
                "nfl_team": "DAL",
            },
            {
                "player_id": "4",
                "player_name": "Kicker",
                "position": "K",
                "nfl_team": "SF",
            },
        ]
    )


def _season_stats() -> pd.DataFrame:
    return pd.DataFrame(
        [
            _stat_row("00-0000001", "Alpha QB", "QB", "SF", passing_yards="3000"),
            _stat_row("00-0000099", "Other QB", "QB", "NYJ", passing_yards="2500"),
            _stat_row("00-0000200", "Other RB", "RB", "SEA", rushing_yards="1000"),
        ]
    )


def _stat_row(
    player_id: str,
    name: str,
    position: str,
    team: str,
    *,
    passing_yards: str = "0",
    rushing_yards: str = "0",
) -> dict[str, str]:
    return {
        "player_id": player_id,
        "player_name": name,
        "player_display_name": name,
        "position": position,
        "recent_team": team,
        "season": "2025",
        "season_type": "REG",
        "passing_yards": passing_yards,
        "passing_tds": "0",
        "passing_interceptions": "0",
        "passing_first_downs": "0",
        "passing_2pt_conversions": "0",
        "rushing_yards": rushing_yards,
        "rushing_tds": "0",
        "rushing_first_downs": "0",
        "rushing_2pt_conversions": "0",
        "receiving_yards": "0",
        "receiving_tds": "0",
        "receiving_first_downs": "0",
        "receiving_2pt_conversions": "0",
        "rushing_fumbles_lost": "0",
        "receiving_fumbles_lost": "0",
        "punt_return_yards": "0",
        "kickoff_return_yards": "0",
        "special_teams_tds": "0",
    }


def _identity_bridge() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "nwr_player_id": "1",
                "sleeper_id": "1",
                "gsis_id": "00-0000001",
                "identity_status": "matched_exact",
                "current_board_player_name": "Alpha QB",
                "current_board_position": "QB",
                "current_board_team": "SF",
            },
            {
                "nwr_player_id": "2",
                "sleeper_id": "2",
                "gsis_id": "00-0000002",
                "identity_status": "matched_exact",
                "current_board_player_name": "Beta RB",
                "current_board_position": "RB",
                "current_board_team": "SEA",
            },
            {
                "nwr_player_id": "3",
                "sleeper_id": "3",
                "gsis_id": "00-0000003",
                "identity_status": "out_of_scope_rookie_or_prospect",
                "current_board_player_name": "Rookie WR",
                "current_board_position": "WR",
                "current_board_team": "DAL",
            },
        ]
    )


def _validation_results() -> pd.DataFrame:
    return pd.DataFrame(
        [
            _validation("QB_T6_THIS_YEAR", "QB", "6", "this_year", "0.10", True),
            _validation("QB_T12_THIS_YEAR", "QB", "12", "this_year", "0.20", True),
            _validation("RB_T24_WITHIN_5Y", "RB", "24", "within_5y", "0.30", True),
            _validation("RB_T36_WITHIN_5Y", "RB", "36", "within_5y", "0.40", True),
            _validation("RB_T6_WITHIN_5Y", "RB", "6", "within_5y", "", False),
            _validation("RB_T12_WITHIN_5Y", "RB", "12", "within_5y", "", False),
            _validation("WR_T6_THIS_YEAR", "WR", "6", "this_year", "0.05", True),
        ]
    )


def _validation(
    field_id: str,
    position: str,
    threshold: str,
    horizon: str,
    baseline: str,
    display_eligible: bool,
) -> dict[str, str]:
    return {
        "field_id": field_id,
        "position": position,
        "threshold": threshold,
        "horizon": horizon,
        "validation_status": (
            "PASS_APP_DISPLAY_VALIDATION"
            if display_eligible
            else "BLOCKED_CALIBRATION_WEAK"
        ),
        "display_eligible": str(display_eligible).lower(),
        "baseline_probability": baseline,
    }


def _model_bucket_rates() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "field_id": "QB_T6_THIS_YEAR",
                "profile_bucket": "prior_threshold_hit",
                "probability": "0.5",
                "baseline_probability": "0.1",
            },
            {
                "field_id": "QB_T12_THIS_YEAR",
                "profile_bucket": "prior_threshold_hit",
                "probability": "0.6",
                "baseline_probability": "0.2",
            },
            {
                "field_id": "RB_T24_WITHIN_5Y",
                "profile_bucket": "limited_or_inactive",
                "probability": "0.2",
                "baseline_probability": "0.3",
            },
            {
                "field_id": "RB_T36_WITHIN_5Y",
                "profile_bucket": "limited_or_inactive",
                "probability": "0.25",
                "baseline_probability": "0.4",
            },
        ]
    )
