from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.services.outcome_v2_identity_bridge_service import (
    DISPLAY_ONLY,
    MODEL_USE_ALLOWED,
    SOURCE_TRUTH_ALLOWED,
    TRAINING_ALLOWED,
    IdentityBridgeSourceMetadata,
    build_outcome_v2_identity_bridge,
    normalize_name,
    write_outcome_v2_identity_bridge_artifacts,
)


def _source_metadata(source_path: Path | None = None) -> IdentityBridgeSourceMetadata:
    return IdentityBridgeSourceMetadata(
        roster_context_path=source_path or Path("roster.csv"),
        roster_pointer_path=None,
        roster_manifest_path=None,
        approval_status="candidate",
        approval_scope="display_stat_context_review_only",
        allowed_use=("display_stat_context_only", "identity_crosscheck"),
        forbidden_use=("private_value", "hidden_sort", "model_training"),
        source_policy_status="identity_crosscheck_candidate_review_only",
    )


def _current_board() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "player_id": "9493",
                "player_name": "Puka Nacua",
                "position": "WR",
                "nfl_team": "LAR",
                "is_rookie": "0",
            },
            {
                "player_id": "no-direct",
                "player_name": "Unique Veteran",
                "position": "RB",
                "nfl_team": "SF",
                "is_rookie": "0",
            },
            {
                "player_id": "name-only",
                "player_name": "Name Only",
                "position": "QB",
                "nfl_team": "",
                "is_rookie": "0",
            },
            {
                "player_id": "ambiguous",
                "player_name": "Ambiguous Back",
                "position": "RB",
                "nfl_team": "DAL",
                "is_rookie": "0",
            },
            {
                "player_id": "12526",
                "player_name": "Tetairoa McMillan",
                "position": "WR",
                "nfl_team": "CAR",
                "is_rookie": "0",
            },
            {
                "player_id": "missing",
                "player_name": "Missing Player",
                "position": "TE",
                "nfl_team": "NYJ",
                "is_rookie": "0",
            },
            {
                "player_id": "kicker",
                "player_name": "Kicker Player",
                "position": "K",
                "nfl_team": "SF",
                "is_rookie": "0",
            },
        ]
    )


def _roster_context() -> pd.DataFrame:
    base = {
        "source_dataset": "rosters",
        "approval_status": "candidate",
        "allowed_use": "display_stat_context_only",
        "blocked_use": "private_value,hidden_sort,model_training",
        "season": "2025",
        "week": "18",
        "status": "ACT",
    }
    return pd.DataFrame(
        [
            {
                **base,
                "sleeper_id": "9493",
                "gsis_id": "00-0039075",
                "full_name": "Puka Nacua",
                "position": "WR",
                "team": "LA",
                "birth_date": "2001-05-29",
                "years_exp": "2",
                "rookie_year": "2023",
            },
            {
                **base,
                "sleeper_id": "multi-key-1",
                "gsis_id": "00-0090001",
                "full_name": "Unique Veteran",
                "position": "RB",
                "team": "SF",
                "birth_date": "1999-01-01",
                "years_exp": "4",
                "rookie_year": "2021",
            },
            {
                **base,
                "sleeper_id": "name-only-candidate",
                "gsis_id": "00-0090002",
                "full_name": "Name Only",
                "position": "QB",
                "team": "LV",
                "birth_date": "1996-01-01",
                "years_exp": "7",
                "rookie_year": "2018",
            },
            {
                **base,
                "sleeper_id": "ambiguous",
                "gsis_id": "00-0090003",
                "full_name": "Ambiguous Back",
                "position": "RB",
                "team": "DAL",
                "birth_date": "1997-01-01",
                "years_exp": "5",
                "rookie_year": "2019",
            },
            {
                **base,
                "sleeper_id": "ambiguous",
                "gsis_id": "00-0090004",
                "full_name": "Ambiguous Back",
                "position": "RB",
                "team": "DAL",
                "birth_date": "1997-01-01",
                "years_exp": "5",
                "rookie_year": "2019",
            },
            {
                **base,
                "sleeper_id": "12526",
                "gsis_id": "00-0040124",
                "full_name": "Tetairoa McMillan",
                "position": "WR",
                "team": "CAR",
                "birth_date": "2003-04-05",
                "years_exp": "0",
                "rookie_year": "2025",
            },
        ]
    )


def _historical_labels() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "player_id": "00-0039075",
                "player_name": "Puka Nacua",
                "position": "WR",
                "season": "2024",
                "team": "LA",
            },
            {
                "player_id": "00-0090001",
                "player_name": "Unique Veteran",
                "position": "RB",
                "season": "2024",
                "team": "SF",
            },
        ]
    )


def _build() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    return build_outcome_v2_identity_bridge(
        _current_board(),
        _roster_context(),
        _historical_labels(),
        source_metadata=_source_metadata(),
    )


def test_normalize_name_removes_suffix_and_punctuation() -> None:
    assert normalize_name("Harold Fannin Jr.") == "haroldfannin"
    assert normalize_name("Amon-Ra St. Brown") == "amonrastbrown"


def test_direct_id_bridge_matches_exact_and_stays_review_only() -> None:
    bridge, audit, _manifest = _build()
    puka = bridge[bridge["nwr_player_id"] == "9493"].iloc[0]
    metrics = dict(zip(audit["metric"], audit["value"], strict=True))

    assert puka["identity_status"] == "matched_exact"
    assert puka["match_method"] == "direct_sleeper_id_to_gsis"
    assert puka["gsis_id"] == "00-0039075"
    assert puka["display_only"] == DISPLAY_ONLY
    assert puka["model_use_allowed"] == MODEL_USE_ALLOWED
    assert puka["source_truth_allowed"] == SOURCE_TRUTH_ALLOWED
    assert puka["training_allowed"] == TRAINING_ALLOWED
    assert metrics["source_policy_status"] == "identity_crosscheck_candidate_review_only"


def test_deterministic_multikey_match_requires_name_position_and_team() -> None:
    bridge, _audit, _manifest = _build()
    unique = bridge[bridge["nwr_player_id"] == "no-direct"].iloc[0]
    name_only = bridge[bridge["nwr_player_id"] == "name-only"].iloc[0]

    assert unique["identity_status"] == "matched_high_confidence"
    assert unique["match_method"] == "deterministic_name_position_team"
    assert unique["gsis_id"] == "00-0090001"
    assert name_only["identity_status"] == "missing_gsis_id"
    assert name_only["gsis_id"] == ""


def test_ambiguous_duplicate_direct_id_is_blocked_for_review() -> None:
    bridge, _audit, _manifest = _build()
    ambiguous = bridge[bridge["nwr_player_id"] == "ambiguous"].iloc[0]

    assert ambiguous["identity_status"] == "ambiguous_review_required"
    assert ambiguous["match_method"] == "ambiguous_direct_sleeper_id_to_gsis"
    assert ambiguous["gsis_id"] == ""


def test_rookie_or_prospect_rows_are_out_of_scope_not_probability_ready() -> None:
    bridge, audit, _manifest = _build()
    rookie = bridge[bridge["nwr_player_id"] == "12526"].iloc[0]
    metrics = dict(zip(audit["metric"], audit["value"], strict=True))

    assert rookie["identity_status"] == "out_of_scope_rookie_or_prospect"
    assert rookie["gsis_id"] == "00-0040124"
    assert rookie["feature_coverage_note"] == "Not enough information"
    assert metrics["out_of_scope_rookie_or_prospect_rows"] == "1"


def test_missing_gsis_rows_are_preserved() -> None:
    bridge, audit, _manifest = _build()
    missing = bridge[bridge["nwr_player_id"] == "missing"].iloc[0]
    metrics = dict(zip(audit["metric"], audit["value"], strict=True))

    assert missing["identity_status"] == "missing_gsis_id"
    assert missing["review_notes"] == (
        "No direct Sleeper ID to GSIS row and no deterministic multi-key match."
    )
    assert metrics["status"] == "PARTIAL_IDENTITY_BRIDGE_BUILT"
    assert metrics["missing_gsis_rows"] == "2"


def test_write_artifacts_creates_review_only_bridge_without_display_probabilities(
    tmp_path: Path,
) -> None:
    board_path = tmp_path / "board.csv"
    roster_path = tmp_path / "roster.csv"
    historical_path = tmp_path / "historical.csv"
    _current_board().to_csv(board_path, index=False)
    _roster_context().to_csv(roster_path, index=False)
    _historical_labels().to_csv(historical_path, index=False)

    result = write_outcome_v2_identity_bridge_artifacts(
        output_root=tmp_path / "out",
        current_board_path=board_path,
        roster_context_pointer_path=None,
        roster_context_path=roster_path,
        historical_season_labels_path=historical_path,
    )

    assert result.status == "PARTIAL_IDENTITY_BRIDGE_BUILT"
    assert result.bridge_rows == 6
    assert result.matched_exact_rows == 1
    assert result.matched_high_confidence_rows == 1
    assert result.missing_gsis_rows == 2
    assert result.ambiguous_rows == 1
    assert result.out_of_scope_rookie_or_prospect_rows == 1
    assert result.bridge_path.exists()
    assert result.audit_path.exists()
    assert result.manifest_path.exists()
    bridge = pd.read_csv(result.bridge_path, dtype=str).fillna("")
    assert not any("probability" in column.lower() for column in bridge.columns)
    assert not any("rank" == column.lower() for column in bridge.columns)
