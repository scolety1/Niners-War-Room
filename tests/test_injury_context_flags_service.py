from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.services.injury_context_flags_service import (
    NOT_ENOUGH_INFORMATION,
    build_enhanced_outcome_display_artifact,
    build_injury_context_flags,
    normalize_injury_context,
    write_injury_context_flags_v0_artifacts,
)


def test_normalize_injury_context_builds_factual_week_counts() -> None:
    summary = normalize_injury_context(_injury_rows())
    alpha_2025 = summary[
        (summary["gsis_id"] == "00-0000001") & (summary["season"] == 2025)
    ].iloc[0]

    assert alpha_2025["injury_report_weeks"] == 3
    assert alpha_2025["out_report_weeks"] == 1
    assert alpha_2025["doubtful_report_weeks"] == 1
    assert alpha_2025["out_or_doubtful_weeks"] == 2
    assert alpha_2025["questionable_report_weeks"] == 1
    assert alpha_2025["medical_projection_made"] == "false"


def test_flags_keep_missing_injury_context_from_becoming_clean_health() -> None:
    flags = _flags()
    beta = flags[flags["nwr_player_id"] == "2"].iloc[0]

    assert beta["prior_season_injury_context_available"] == NOT_ENOUGH_INFORMATION
    assert beta["prior_season_injury_report_weeks"] == NOT_ENOUGH_INFORMATION
    assert "missing injury context is not clean health" in beta["availability_caveat"]
    assert beta["injury_used_as_model_input"] == "false"
    assert beta["medical_projection_made"] == "false"


def test_missing_feature_rows_get_not_enough_information_reason() -> None:
    flags = _flags()
    beta = flags[flags["nwr_player_id"] == "2"].iloc[0]

    assert beta["eligibility_status"] == "missing_current_feature_coverage"
    assert beta["limited_recent_sample"] == "true_missing_2025_feature_row"
    assert beta["missed_prior_season_context_flag"] == "true_missing_2025_feature_row"
    assert "No approved 2025 Outcome V2 feature row" in beta["not_enough_information_reason"]
    assert NOT_ENOUGH_INFORMATION in beta["not_enough_information_reason"]


def test_rookies_remain_out_of_scope_and_do_not_gain_probabilities() -> None:
    flags = _flags()
    rookie = flags[flags["nwr_player_id"] == "3"].iloc[0]

    assert rookie["eligibility_status"] == "out_of_scope_rookie_or_prospect"
    assert rookie["limited_recent_sample"] == "out_of_scope_rookie_or_prospect"
    assert rookie["missed_prior_season_context_flag"] == "out_of_scope_rookie_or_prospect"
    assert "does not create rookie probabilities" in rookie["not_enough_information_reason"]


def test_enhanced_artifact_preserves_outcome_values_and_adds_flags() -> None:
    outcome = _outcome_display()
    flags = _flags()
    enhanced = build_enhanced_outcome_display_artifact(outcome, flags)

    assert len(enhanced) == len(outcome)
    assert enhanced["QB T12 This Year"].tolist() == outcome["QB T12 This Year"].tolist()
    assert enhanced["RB T24 Within 5Y"].tolist() == outcome["RB T24 Within 5Y"].tolist()
    assert "injury_context_available" in enhanced.columns
    assert "injury_risk_score" not in enhanced.columns
    assert "rank_adjustment" not in enhanced.columns
    assert set(enhanced["injury_used_as_model_input"]) == {"false"}
    assert set(enhanced["medical_projection_made"]) == {"false"}


def test_writer_creates_review_only_outputs_without_raw_shared_commit(tmp_path: Path) -> None:
    injury_path = tmp_path / "injuries.csv"
    outcome_path = tmp_path / "outcome.csv"
    labels_path = tmp_path / "labels.csv"
    output_root = tmp_path / "shared_out"
    enhanced_path = tmp_path / "docs" / "enhanced.csv"

    _injury_rows().to_csv(injury_path, index=False)
    _outcome_display().to_csv(outcome_path, index=False)
    _season_labels().to_csv(labels_path, index=False)

    result = write_injury_context_flags_v0_artifacts(
        output_root=output_root,
        enhanced_artifact_path=enhanced_path,
        injury_raw_path=injury_path,
        outcome_display_path=outcome_path,
        season_label_path=labels_path,
    )
    enhanced = pd.read_csv(result.enhanced_artifact_path, dtype=str).fillna("")
    manifest = pd.read_csv(result.manifest_path, dtype=str).fillna("")

    assert result.flag_rows == 3
    assert result.enhanced_rows == 3
    assert result.prior_season_context_rows == 2
    assert result.missing_feature_rows == 1
    assert result.rookie_out_of_scope_rows == 1
    assert result.sha256
    assert set(enhanced["injury_context_review_only"]) == {"true"}
    assert set(enhanced["injury_used_as_model_input"]) == {"false"}
    assert set(enhanced["medical_projection_made"]) == {"false"}
    assert set(manifest["model_use_allowed"]) == {"false"}
    assert set(manifest["app_wiring_allowed"]) == {"false"}


def _flags() -> pd.DataFrame:
    return build_injury_context_flags(
        _outcome_display(),
        normalize_injury_context(_injury_rows()),
        _season_labels(),
    )


def _injury_rows() -> pd.DataFrame:
    return pd.DataFrame(
        [
            _injury_row("2025", "1", "SF", "00-0000001", "Alpha QB", "QB", "Out"),
            _injury_row("2025", "2", "SF", "00-0000001", "Alpha QB", "QB", "Doubtful"),
            _injury_row(
                "2025",
                "3",
                "SF",
                "00-0000001",
                "Alpha QB",
                "QB",
                "Questionable",
            ),
            _injury_row("2024", "7", "SF", "00-0000002", "Beta RB", "RB", "Out"),
            _injury_row("2025", "4", "DAL", "00-0000003", "Rookie WR", "WR", "Out"),
        ]
    )


def _injury_row(
    season: str,
    week: str,
    team: str,
    gsis_id: str,
    full_name: str,
    position: str,
    report_status: str,
) -> dict[str, str]:
    return {
        "season": season,
        "game_type": "REG",
        "team": team,
        "week": week,
        "gsis_id": gsis_id,
        "position": position,
        "full_name": full_name,
        "report_primary_injury": "knee",
        "report_secondary_injury": "",
        "report_status": report_status,
        "practice_primary_injury": "",
        "practice_secondary_injury": "",
        "practice_status": "Did Not Participate In Practice",
        "date_modified": "2026-01-01",
    }


def _outcome_display() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "nwr_player_id": "1",
                "sleeper_id": "1",
                "gsis_id": "00-0000001",
                "player_name": "Alpha QB",
                "position": "QB",
                "team": "SF",
                "eligibility_status": "eligible_veteran_feature_covered",
                "identity_status": "matched_exact",
                "feature_coverage_status": "feature_covered_2025_regular_season",
                "availability_context_status": "partial_availability_context_missing_games",
                "caveat_summary": "games missing",
                "QB T12 This Year": "55.0%",
                "RB T24 Within 5Y": NOT_ENOUGH_INFORMATION,
            },
            {
                "nwr_player_id": "2",
                "sleeper_id": "2",
                "gsis_id": "00-0000002",
                "player_name": "Beta RB",
                "position": "RB",
                "team": "SEA",
                "eligibility_status": "missing_current_feature_coverage",
                "identity_status": "matched_exact",
                "feature_coverage_status": "missing_2025_feature_row",
                "availability_context_status": "partial_availability_context_missing_games",
                "caveat_summary": "missing feature row",
                "QB T12 This Year": NOT_ENOUGH_INFORMATION,
                "RB T24 Within 5Y": NOT_ENOUGH_INFORMATION,
            },
            {
                "nwr_player_id": "3",
                "sleeper_id": "3",
                "gsis_id": "00-0000003",
                "player_name": "Rookie WR",
                "position": "WR",
                "team": "DAL",
                "eligibility_status": "out_of_scope_rookie_or_prospect",
                "identity_status": "matched_exact",
                "feature_coverage_status": "rookie_or_prospect_out_of_scope",
                "availability_context_status": "rookie_or_prospect_out_of_scope",
                "caveat_summary": "rookie out of scope",
                "QB T12 This Year": NOT_ENOUGH_INFORMATION,
                "RB T24 Within 5Y": NOT_ENOUGH_INFORMATION,
            },
        ]
    )


def _season_labels() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "player_id": "00-0000001",
                "season": "2025",
                "fantasy_points": "220",
                "position_finish": "12",
                "games_played": "14",
            },
            {
                "player_id": "00-0000002",
                "season": "2024",
                "fantasy_points": "110",
                "position_finish": "30",
                "games_played": "8",
            },
        ]
    )
