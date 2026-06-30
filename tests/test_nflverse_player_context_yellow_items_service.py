from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from src.services.nflverse_player_context_yellow_items_service import (
    DENY,
    DISPLAY_ONLY,
    KEEP_NEED_IDENTITY_REVIEW,
    NEED_CURRENT_SCHEDULE_REFRESH,
    NOT_ENOUGH_INFORMATION,
    SAFE_RESOLUTION_PROPOSED,
    build_identity_review,
    build_schedule_audit,
    write_nflverse_player_context_yellow_item_docs,
)


def test_identity_review_builds_exact_candidate_proposal_without_auto_approval(
    tmp_path: Path,
) -> None:
    artifact, snapshot = _write_identity_fixture(tmp_path)

    result = build_identity_review(artifact_path=artifact, snapshot_dir=snapshot)

    assert result.reviewed_rows == 2
    assert result.safe_resolution_proposals == 1
    assert result.keep_review_rows == 1
    proposal = result.proposal_rows[0]
    assert proposal["nwr_player_name"] == "Jeremiyah Love"
    assert proposal["candidate_gsis_id"] == "LOV121782"
    assert proposal["candidate_sleeper_id"] == "13287"
    assert proposal["proposed_decision"] == SAFE_RESOLUTION_PROPOSED
    assert proposal["review_only"] == DISPLAY_ONLY
    assert proposal["model_use_allowed"] == DENY
    assert proposal["training_allowed"] == DENY
    assert proposal["source_truth_allowed"] == DENY


def test_identity_review_keeps_missing_candidate_under_review(tmp_path: Path) -> None:
    artifact, snapshot = _write_identity_fixture(tmp_path)

    result = build_identity_review(artifact_path=artifact, snapshot_dir=snapshot)

    missing = next(row for row in result.queue_rows if row["nwr_player_name"] == "No Match")
    assert missing["candidate_gsis_ids"] == NOT_ENOUGH_INFORMATION
    assert missing["proposed_decision"] == KEEP_NEED_IDENTITY_REVIEW
    assert missing["confidence"] == "low"


def test_schedule_audit_flags_stale_schedule_without_fake_context(tmp_path: Path) -> None:
    artifact, snapshot = _write_schedule_fixture(tmp_path)

    result = build_schedule_audit(
        artifact_path=artifact,
        snapshot_dir=snapshot,
        as_of=date(2026, 6, 30),
    )

    ari = next(row for row in result.audit_rows if row["team"] == "ARI")
    assert ari["schedule_context_status"] == NEED_CURRENT_SCHEDULE_REFRESH
    assert ari["has_current_or_future_game"] == "false"
    assert ari["next_game_week"] == NOT_ENOUGH_INFORMATION
    assert ari["next_opponent"] == NOT_ENOUGH_INFORMATION
    assert ari["bye_week"] == NOT_ENOUGH_INFORMATION
    assert ari["display_only"] == DISPLAY_ONLY
    assert ari["model_use_allowed"] == DENY
    assert result.teams_with_current_or_future_game == 0


def test_yellow_item_docs_write_required_outputs(tmp_path: Path) -> None:
    artifact, snapshot = _write_identity_fixture(tmp_path)
    _write_schedule_files(snapshot)
    identity_dir = tmp_path / "identity_docs"
    schedule_dir = tmp_path / "schedule_docs"

    result = write_nflverse_player_context_yellow_item_docs(
        artifact_path=artifact,
        snapshot_dir=snapshot,
        identity_output_dir=identity_dir,
        schedule_output_dir=schedule_dir,
        as_of=date(2026, 6, 30),
    )

    assert result.artifact_rebuild_recommended is False
    assert (identity_dir / "nflverse_player_context_identity_review_queue.csv").exists()
    assert (
        identity_dir / "nflverse_player_context_identity_resolution_proposals.csv"
    ).exists()
    assert (identity_dir / "nflverse_player_context_identity_review_summary.md").exists()
    assert (schedule_dir / "nflverse_schedule_context_audit.csv").exists()
    assert (schedule_dir / "nflverse_schedule_context_build_report.md").exists()
    assert (schedule_dir / "nflverse_schedule_context_guardrail_report.md").exists()


def _write_identity_fixture(tmp_path: Path) -> tuple[Path, Path]:
    artifact = tmp_path / "artifact.csv"
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    _write_csv(
        artifact,
        [
            _artifact_row("Jeremiyah Love", "RB", "ARI"),
            _artifact_row("No Match", "WR", "FA"),
        ],
    )
    _write_csv(
        snapshot / "ff_playerids.csv",
        [
            {
                "name": "Jeremiyah Love",
                "player_name": "Jeremiyah Love",
                "position": "RB",
                "team": "ARI",
                "gsis_id": "LOV121782",
                "sleeper_id": "13287",
            }
        ],
    )
    _write_csv(
        snapshot / "players.csv",
        [
            {
                "display_name": "Jeremiyah Love",
                "position": "RB",
                "latest_team": "ARI",
                "gsis_id": "LOV121782",
            }
        ],
    )
    _write_csv(
        snapshot / "rosters.csv",
        [
            {
                "full_name": "Roster Player",
                "position": "RB",
                "team": "ARI",
                "gsis_id": "00-0000001",
                "sleeper_id": "1",
            }
        ],
    )
    _write_csv(
        snapshot / "weekly_rosters.csv",
        [
            {
                "full_name": "Roster Player",
                "position": "RB",
                "team": "ARI",
                "gsis_id": "00-0000001",
                "sleeper_id": "1",
            }
        ],
    )
    return artifact, snapshot


def _write_schedule_fixture(tmp_path: Path) -> tuple[Path, Path]:
    artifact = tmp_path / "artifact.csv"
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    _write_csv(artifact, [_artifact_row("Player One", "RB", "ARI", safe=True)])
    _write_schedule_files(snapshot)
    return artifact, snapshot


def _write_schedule_files(snapshot: Path) -> None:
    _write_csv(
        snapshot / "schedules.csv",
        [
            {
                "game_id": "2025_01_ARI_SEA",
                "season": "2025",
                "week": "1",
                "gameday": "2025-09-07",
                "home_team": "ARI",
                "away_team": "SEA",
            }
        ],
    )
    _write_csv(
        snapshot / "teams.csv",
        [
            {
                "team_abbr": "ARI",
                "team_name": "Arizona Cardinals",
            }
        ],
    )


def _artifact_row(name: str, position: str, team: str, *, safe: bool = False) -> dict[str, str]:
    return {
        "nwr_player_id": NOT_ENOUGH_INFORMATION,
        "nwr_player_name": name,
        "nwr_position": position,
        "nwr_team": team,
        "nflverse_team": team if safe else NOT_ENOUGH_INFORMATION,
        "identity_join_status": "SAFE_NOW_DISPLAY_ONLY" if safe else "NEED_IDENTITY_REVIEW",
        "identity_caveat": "exact" if safe else "no_safe_nflverse_identity_match",
    }


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
