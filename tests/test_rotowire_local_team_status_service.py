from __future__ import annotations

import csv
from pathlib import Path

from src.services.rotowire_local_team_status_service import (
    BLOCKED_USE,
    NORMALIZED_ROTOWIRE_HEADER,
    build_rotowire_team_status_source,
    rotowire_team_status_lookup,
    select_rotowire_team_status_row,
    write_rotowire_team_status_source,
)


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def test_rotowire_normalizer_writes_expected_schema_from_fixture(tmp_path: Path) -> None:
    workout = tmp_path / "workout.csv"
    depth = tmp_path / "depth.csv"
    _write_csv(
        workout,
        [
            {
                "source": "RotoWire",
                "source_file": "local",
                "collected_at_utc": "2026-05-25T23:12:00+00:00",
                "position": "WR",
                "player": "Example Player",
                "team": "FA",
                "draft_year": "2020",
                "event": "Combine",
            }
        ],
    )
    _write_csv(
        depth,
        [
            {
                "source": "RotoWire",
                "source_file": "local_depth",
                "collected_at_utc": "2026-05-22T06:00:00+00:00",
                "team": "Vikings",
                "position": "WR",
                "depth_rank": "3",
                "slot": "WR #3",
                "player": "Roster Player",
                "status": "Ques",
                "raw_player_cell": "Roster Player - Ques",
            }
        ],
    )

    result = build_rotowire_team_status_source(
        workout_path=workout,
        depth_chart_path=depth,
    )
    paths = write_rotowire_team_status_source(
        result=result,
        review_rows=tmp_path / "rows.csv",
        manifest_path=tmp_path / "manifest.csv",
        discovery_report_path=tmp_path / "discovery.md",
        source_contract_path=tmp_path / "contract.md",
    )

    assert paths.review_rows.exists()
    with paths.review_rows.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert tuple(rows[0].keys()) == NORMALIZED_ROTOWIRE_HEADER
    assert rows[0]["status"] == "free_agent_or_no_team"
    assert rows[0]["nfl_team"] == ""
    assert rows[1]["nfl_team"] == "MIN"
    assert rows[1]["injury_status"] == "Ques"


def test_rotowire_blocked_use_forbids_private_score_contamination() -> None:
    assert "do_not_use_for_nwr_dynasty_score" in BLOCKED_USE
    assert "nwr_rank" in BLOCKED_USE
    assert "outcome_percentages" in BLOCKED_USE


def test_rotowire_lookup_uses_exact_name_position_and_handles_no_team(
    tmp_path: Path,
) -> None:
    rows_path = tmp_path / "rotowire_rows.csv"
    with rows_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=NORMALIZED_ROTOWIRE_HEADER)
        writer.writeheader()
        writer.writerow(
            {
                "source_provider": "rotowire",
                "source_file": "fixture",
                "source_as_of_date": "2026-05-25",
                "source_loaded_at": "2026-06-08",
                "source_row_id": "1",
                "full_name": "Exact Player",
                "search_full_name": "exactplayer",
                "position": "WR",
                "nfl_team": "",
                "team_abbr_raw": "FA",
                "status": "free_agent_or_no_team",
                "allowed_use": "current_team_status_display",
                "blocked_use": BLOCKED_USE,
                "raw_source_payload_hash": "hash",
                "source_confidence": "fixture",
            }
        )

    lookup = rotowire_team_status_lookup(rows_path)
    selected = select_rotowire_team_status_row(lookup[("exactplayer", "WR")])

    assert selected["status"] == "free_agent_or_no_team"
    assert selected["nfl_team"] == ""


def test_rotowire_ambiguous_team_matches_are_not_selected() -> None:
    selected = select_rotowire_team_status_row(
        (
            {"full_name": "A", "position": "WR", "nfl_team": "MIN", "status": "active"},
            {"full_name": "A", "position": "WR", "nfl_team": "SF", "status": "active"},
        )
    )

    assert selected == {}
