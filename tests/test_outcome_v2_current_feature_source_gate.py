from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.services.outcome_v2_current_feature_source_gate import (
    APPROVED_ALLOWED_USE,
    evaluate_current_feature_source_gate,
    write_current_feature_source_gate_artifacts,
)


def test_gate_partially_approves_display_only_when_games_are_missing() -> None:
    decision, audit = evaluate_current_feature_source_gate(
        _season_stats(include_games=False),
        _identity_bridge(include_unmatched=False),
        _validation_results(),
        pointer_metadata=_pointer_metadata(),
        manifest_metadata=_manifest_metadata(),
    )
    metrics = _metrics(audit)

    assert decision == "PARTIAL_APPROVAL_2025_FEATURE_CONTEXT_OUTCOME_V2_DISPLAY_ONLY"
    assert metrics["field_status"] == "PARTIAL_FIELD_COMPATIBILITY"
    assert metrics["availability_status"] == "PARTIAL_AVAILABILITY_CONTEXT_MISSING_GAMES"
    assert metrics["matched_feature_rows"] == "1"
    assert metrics["missing_feature_rows"] == "0"
    assert metrics["allowed_use_if_approved"] == APPROVED_ALLOWED_USE
    assert metrics["display_only"] == "true"
    assert metrics["model_use_allowed"] == "false"
    assert metrics["source_truth_allowed"] == "false"
    assert metrics["training_allowed"] == "false"


def test_unknown_timing_blocks_approval() -> None:
    decision, _audit = evaluate_current_feature_source_gate(
        _season_stats(season="2024"),
        _identity_bridge(include_unmatched=False),
        _validation_results(),
        pointer_metadata=_pointer_metadata(),
        manifest_metadata=_manifest_metadata(),
    )

    assert decision == "BLOCKED_UNKNOWN_TIMING"


def test_missing_required_scoring_field_blocks_approval() -> None:
    stats = _season_stats(include_games=True).drop(columns=["passing_first_downs"])

    decision, audit = evaluate_current_feature_source_gate(
        stats,
        _identity_bridge(include_unmatched=False),
        _validation_results(),
        pointer_metadata=_pointer_metadata(),
        manifest_metadata=_manifest_metadata(),
    )
    metrics = _metrics(audit)

    assert decision == "BLOCKED_FIELD_MISMATCH"
    assert metrics["field_status"] == "BLOCKED_FIELD_MISMATCH"
    assert "passing_first_downs" in metrics["required_missing_columns"]


def test_missing_identity_bridge_match_blocks_approval() -> None:
    decision, audit = evaluate_current_feature_source_gate(
        _season_stats(include_games=True).iloc[0:0],
        _identity_bridge(include_unmatched=False),
        _validation_results(),
        pointer_metadata=_pointer_metadata(),
        manifest_metadata=_manifest_metadata(),
    )
    metrics = _metrics(audit)

    assert decision == "BLOCKED_UNKNOWN_TIMING"
    assert metrics["identity_status"] == "BLOCKED_IDENTITY_JOIN"


def test_blocked_source_policy_blocks_approval() -> None:
    pointer = _pointer_metadata()
    pointer["allowed_use"] = ["source_audit"]

    decision, audit = evaluate_current_feature_source_gate(
        _season_stats(include_games=True),
        _identity_bridge(include_unmatched=False),
        _validation_results(),
        pointer_metadata=pointer,
        manifest_metadata=_manifest_metadata(),
    )
    metrics = _metrics(audit)

    assert decision == "BLOCKED_SOURCE_POLICY"
    assert metrics["source_policy_status"] == "BLOCKED_SOURCE_POLICY"


def test_writer_creates_review_only_audit_artifacts(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    source_root.mkdir()
    stats_path = source_root / "player_season_stats_display_context.csv"
    manifest_path = source_root / "manifest.json"
    pointer_path = tmp_path / "latest_candidate.json"
    bridge_path = tmp_path / "bridge.csv"
    validation_path = tmp_path / "validation.csv"

    _season_stats(include_games=False).to_csv(stats_path, index=False)
    manifest_path.write_text(json.dumps(_manifest_metadata(source_root)), encoding="utf-8")
    pointer = _pointer_metadata(source_root, manifest_path)
    pointer_path.write_text(json.dumps(pointer), encoding="utf-8")
    _identity_bridge(include_unmatched=False).to_csv(bridge_path, index=False)
    _validation_results().to_csv(validation_path, index=False)

    result = write_current_feature_source_gate_artifacts(
        output_root=tmp_path / "out",
        season_stats_pointer_path=pointer_path,
        identity_bridge_path=bridge_path,
        validation_results_path=validation_path,
    )

    assert result.decision == "PARTIAL_APPROVAL_2025_FEATURE_CONTEXT_OUTCOME_V2_DISPLAY_ONLY"
    assert result.audit_path.exists()
    assert result.manifest_path.exists()
    manifest = pd.read_csv(result.manifest_path, dtype=str).fillna("")
    assert set(manifest["display_only"]) == {"true"}
    assert set(manifest["model_use_allowed"]) == {"false"}
    assert set(manifest["source_truth_allowed"]) == {"false"}
    assert set(manifest["training_allowed"]) == {"false"}


def _metrics(audit: pd.DataFrame) -> dict[str, str]:
    return dict(zip(audit["metric"], audit["value"], strict=True))


def _season_stats(*, include_games: bool = False, season: str = "2025") -> pd.DataFrame:
    row = {
        "source_dataset": "season_stats",
        "approval_status": "candidate",
        "allowed_use": "display_stat_context_only",
        "blocked_use": "private_value,hidden_sort,model_training",
        "source_timing_class": "unknown_timing_yellow",
        "live_use_allowed": "False",
        "timing_notes": "complete regular season row for test",
        "player_id": "00-0000001",
        "player_name": "A.Player",
        "player_display_name": "Alpha Player",
        "position": "QB",
        "position_group": "QB",
        "recent_team": "SF",
        "season": season,
        "season_type": "REG",
        "completions": "1",
        "attempts": "1",
        "passing_yards": "300",
        "passing_tds": "2",
        "passing_interceptions": "1",
        "passing_first_downs": "20",
        "passing_2pt_conversions": "0",
        "carries": "2",
        "rushing_yards": "20",
        "rushing_tds": "0",
        "rushing_first_downs": "1",
        "rushing_2pt_conversions": "0",
        "targets": "0",
        "receptions": "0",
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
    if include_games:
        row["games"] = "17"
    return pd.DataFrame([row])


def _identity_bridge(*, include_unmatched: bool) -> pd.DataFrame:
    rows = [
        {
            "nwr_player_id": "1",
            "current_board_player_name": "Alpha Player",
            "current_board_position": "QB",
            "current_board_team": "SF",
            "gsis_id": "00-0000001",
            "identity_status": "matched_exact",
        },
        {
            "nwr_player_id": "rookie",
            "current_board_player_name": "Rookie Player",
            "current_board_position": "WR",
            "current_board_team": "SF",
            "gsis_id": "00-0000003",
            "identity_status": "out_of_scope_rookie_or_prospect",
        },
    ]
    if include_unmatched:
        rows.append(
            {
                "nwr_player_id": "2",
                "current_board_player_name": "Beta Player",
                "current_board_position": "WR",
                "current_board_team": "SEA",
                "gsis_id": "00-0000002",
                "identity_status": "matched_exact",
            }
        )
    return pd.DataFrame(rows)


def _validation_results() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "field_id": "QB_T6_THIS_YEAR",
                "validation_status": "PASS_APP_DISPLAY_VALIDATION",
            },
            {
                "field_id": "RB_T6_WITHIN_5Y",
                "validation_status": "BLOCKED_CALIBRATION_WEAK",
            },
        ]
    )


def _pointer_metadata(source_root: Path | None = None, manifest_path: Path | None = None) -> dict:
    root = source_root or Path(r"C:\fake\source")
    return {
        "allowed_use": ["display_stat_context_only", "source_audit"],
        "approval_scope": "display_stat_context_review_only",
        "approval_status": "candidate",
        "data_file": "player_season_stats_display_context.csv",
        "forbidden_use": ["private_value", "hidden_sort", "hidden_rank", "model_training"],
        "live_use_allowed": False,
        "manifest_path": str(manifest_path or root / "manifest.json"),
        "snapshot_path": str(root),
        "source_timing_classes": ["unknown_timing_yellow"],
    }


def _manifest_metadata(source_root: Path | None = None) -> dict:
    root = source_root or Path(r"C:\fake\source")
    return {
        "allowed_use": ["display_stat_context_only", "source_audit"],
        "approval_status": "candidate",
        "approved_for": ["display_stat_context_review_only"],
        "contains_adp": False,
        "contains_market_data": False,
        "contains_private_value": False,
        "data_file": "player_season_stats_display_context.csv",
        "forbidden_use": ["private_value", "hidden_sort", "hidden_rank", "model_training"],
        "live_use_allowed": False,
        "package_name": "stats_context/player_season_stats_display_context",
        "row_count": 1,
        "schema_version": "nflverse_normalizer_v0",
        "snapshot_label": "test",
        "source_branch": "local_only_scheduled_ingest",
        "source_created_at": "2026-06-21T06:09:39.128408+00:00",
        "source_datasets": ["season_stats"],
        "source_head": str(root),
        "source_lane": "stats_context",
        "source_repo": "nflverse/nflreadpy local raw snapshot",
        "source_timing_classes": ["unknown_timing_yellow"],
    }
