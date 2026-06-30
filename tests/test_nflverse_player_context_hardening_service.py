from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from src.services.nflverse_player_context_hardening_service import (
    DENY,
    DISPLAY_ONLY,
    write_nflverse_player_context_hardening_docs,
)


def test_hardening_docs_keep_identity_proposals_unapproved(tmp_path: Path) -> None:
    paths = _write_fixture(tmp_path)

    result = write_nflverse_player_context_hardening_docs(
        output_dir=tmp_path / "out",
        artifact_path=paths["artifact"],
        join_health_path=paths["join_health"],
        identity_queue_path=paths["identity_queue"],
        identity_proposals_path=paths["identity_proposals"],
        schedule_snapshot_dir=paths["schedule_snapshot"],
        as_of=date(2026, 6, 30),
    )

    packet = _read_csv(tmp_path / "out" / "identity_resolution_human_review_packet.csv")
    assert result.artifact_rows == 1
    assert result.safe_rows == 1
    assert result.identity_review_rows == 1
    assert result.identity_proposals == 1
    assert result.schedule_future_rows == 1
    assert packet[0]["approved_by_human"] == DENY
    assert packet[0]["display_only"] == DISPLAY_ONLY
    assert packet[0]["model_use_allowed"] == DENY
    assert packet[0]["training_allowed"] == DENY
    assert packet[0]["source_truth_allowed"] == DENY
    assert packet[0]["decision_needed"] == "SAFE_RESOLUTION_PROPOSED"


def test_hardening_docs_write_reports_and_app_lane_guide(tmp_path: Path) -> None:
    paths = _write_fixture(tmp_path)

    write_nflverse_player_context_hardening_docs(
        output_dir=tmp_path / "out",
        artifact_path=paths["artifact"],
        join_health_path=paths["join_health"],
        identity_queue_path=paths["identity_queue"],
        identity_proposals_path=paths["identity_proposals"],
        schedule_snapshot_dir=paths["schedule_snapshot"],
        as_of=date(2026, 6, 30),
    )

    qa = (tmp_path / "out" / "player_context_artifact_qa_report.md").read_text(
        encoding="utf-8"
    )
    schedule = (tmp_path / "out" / "schedule_future_coverage_audit.md").read_text(
        encoding="utf-8"
    )
    guide = (tmp_path / "out" / "APP_LANE_CONSUMPTION_GUIDE_20260630.md").read_text(
        encoding="utf-8"
    )
    assert "Artifact rows: `1`" in qa
    assert "Current/future rows as of 2026-06-30: `1`" in schedule
    assert "Never read raw `C:\\NWR_SHARED_DATA` from app pages." in guide
    assert "Identity proposals are not approved joins." in guide


def _write_fixture(tmp_path: Path) -> dict[str, Path]:
    artifact = tmp_path / "artifact.csv"
    join_health = tmp_path / "join_health.csv"
    identity_queue = tmp_path / "identity_queue.csv"
    identity_proposals = tmp_path / "identity_proposals.csv"
    schedule_snapshot = tmp_path / "schedule"
    schedule_snapshot.mkdir()
    _write_csv(
        artifact,
        [
            {
                "nwr_player_id": "11566",
                "nwr_player_name": "Drake Maye",
                "nwr_position": "QB",
                "nwr_team": "NE",
                "nflverse_gsis_id": "00-0039150",
                "nflverse_sleeper_id": "11566",
                "nflverse_player_name": "Drake Maye",
                "nflverse_team": "NE",
                "nflverse_position": "QB",
                "identity_join_status": "SAFE_NOW_DISPLAY_ONLY",
                "review_required": "false",
                "next_game_context": "season=2026; week=1; date=2026-09-13",
                "opponent_context": "opponent=NYJ; home_away=home",
                "bye_context": "week=7",
                "contract_context": "active=True; team=NE; year_signed=2025; years=4",
                "injury_report_date_week": "season=2025; week=2",
                "latest_snap_season": "2025",
                "draft_round": "1",
                "model_use_allowed": "false",
                "training_allowed": "false",
                "source_truth_allowed": "false",
                "rank_logic_allowed": "false",
                "hidden_sort_allowed": "false",
                "trade_value_allowed": "false",
                "pick_value_allowed": "false",
            }
        ],
    )
    _write_csv(
        join_health,
        [
            {
                "gate": "next_game_bye_gate",
                "clean_join_rows": "1",
            }
        ],
    )
    identity_row = {
        "nwr_player_id": "Not enough information",
        "nwr_player_name": "Jeremiyah Love",
        "nwr_position": "RB",
        "nwr_team": "ARI",
        "proposed_decision": "SAFE_RESOLUTION_PROPOSED",
        "candidate_gsis_id": "LOV121782",
        "candidate_sleeper_id": "13287",
        "candidate_source": "ff_playerids",
        "confidence": "high",
        "notes": "proposal only",
    }
    _write_csv(identity_queue, [identity_row])
    _write_csv(identity_proposals, [identity_row])
    _write_csv(
        schedule_snapshot / "schedules.csv",
        [
            {
                "season": "2026",
                "week": "1",
                "gameday": "2026-09-13",
                "home_team": "NE",
                "away_team": "NYJ",
            }
        ],
    )
    return {
        "artifact": artifact,
        "join_health": join_health,
        "identity_queue": identity_queue,
        "identity_proposals": identity_proposals,
        "schedule_snapshot": schedule_snapshot,
    }


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))
