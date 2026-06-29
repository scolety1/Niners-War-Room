from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.services.outcome_v2_current_identity_bridge_gate import (
    NOT_ENOUGH_INFORMATION,
    build_current_identity_bridge_audit,
    normalize_name,
    write_current_identity_bridge_gate_artifacts,
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
                "player_id": "12526",
                "player_name": "Tetairoa McMillan",
                "position": "WR",
                "nfl_team": "CAR",
                "is_rookie": "0",
            },
            {
                "player_id": "k1",
                "player_name": "Kicker One",
                "position": "K",
                "nfl_team": "SF",
                "is_rookie": "0",
            },
        ]
    )


def _identity_audit(*, with_gsis: bool = False) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "player_name": "Puka Nacua",
                "position": "WR",
                "sleeper_id": "9493",
                "nflverse_id_or_gsis": "00-0039075" if with_gsis else "",
                "match_method": "exact_sleeper_to_gsis",
                "match_confidence": "100",
                "needs_manual_review": "false",
            },
            {
                "player_name": "Tetairoa McMillan",
                "position": "WR",
                "sleeper_id": "12526",
                "nflverse_id_or_gsis": "",
                "match_method": "exact_name_position_sleeper",
                "match_confidence": "100",
                "needs_manual_review": "false",
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
            }
        ]
    )


def test_normalize_name_removes_suffix_and_punctuation() -> None:
    assert normalize_name("Amon-Ra St. Brown Jr.") == "amonrastbrown"


def test_gate_blocks_when_identity_audit_has_no_approved_gsis_bridge() -> None:
    audit, summary = build_current_identity_bridge_audit(
        _current_board(),
        _identity_audit(with_gsis=False),
        _historical_labels(),
    )
    metrics = dict(zip(summary["metric"], summary["value"], strict=True))
    puka = audit[audit["current_player_id"] == "9493"].iloc[0]
    rookie_like = audit[audit["current_player_id"] == "12526"].iloc[0]

    assert metrics["gate_status"] == "BLOCKED_NO_APPROVED_COMPACT_GSIS_BRIDGE"
    assert metrics["eligible_qb_rb_wr_te_rows"] == "2"
    assert metrics["approved_bridge_rows"] == "0"
    assert metrics["diagnostic_name_position_matches"] == "1"
    assert puka["approved_bridge_status"] == "blocked_missing_gsis"
    assert puka["diagnostic_name_position_gsis_id"] == "00-0039075"
    assert puka["display_artifact_allowed"] == "no"
    assert puka["current_feature_status"] == NOT_ENOUGH_INFORMATION
    assert rookie_like["out_of_scope_status"] == "out_of_scope_rookie_or_prospect"
    assert rookie_like["blocker"] == "rookie_outcome_separate_lane_blocked"


def test_gate_counts_approved_bridge_but_still_blocks_partial_coverage() -> None:
    audit, summary = build_current_identity_bridge_audit(
        _current_board(),
        _identity_audit(with_gsis=True),
        _historical_labels(),
    )
    metrics = dict(zip(summary["metric"], summary["value"], strict=True))
    puka = audit[audit["current_player_id"] == "9493"].iloc[0]

    assert puka["approved_bridge_status"] == "approved_gsis_bridge"
    assert puka["approved_gsis_id"] == "00-0039075"
    assert metrics["approved_bridge_rows"] == "1"
    assert metrics["gate_status"] == "BLOCKED_NO_APPROVED_COMPACT_GSIS_BRIDGE"


def test_write_artifacts_stays_review_only_and_creates_no_display_file(tmp_path: Path) -> None:
    board_path = tmp_path / "board.csv"
    identity_path = tmp_path / "identity.csv"
    historical_path = tmp_path / "historical.csv"
    _current_board().to_csv(board_path, index=False)
    _identity_audit(with_gsis=False).to_csv(identity_path, index=False)
    _historical_labels().to_csv(historical_path, index=False)

    result = write_current_identity_bridge_gate_artifacts(
        output_root=tmp_path / "out",
        current_board_path=board_path,
        identity_audit_path=identity_path,
        historical_season_labels_path=historical_path,
    )

    assert result.status == "BLOCKED_NO_APPROVED_COMPACT_GSIS_BRIDGE"
    assert result.eligible_rows == 2
    assert result.approved_bridge_rows == 0
    assert result.diagnostic_name_position_matches == 1
    assert result.current_display_artifact_created is False
    assert result.audit_path.exists()
    assert result.summary_path.exists()
    assert result.manifest_path.exists()
    assert not (tmp_path / "out" / "outcome_v2_current_player_display.csv").exists()
