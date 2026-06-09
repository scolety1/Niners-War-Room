from __future__ import annotations

import csv
from pathlib import Path

from src.data.csv_schemas import CSV_SCHEMAS, REQUIRED_V1_FILES
from src.services.data_pack_diff_service import (
    build_data_pack_diff_report,
    diff_detail_rows,
    diff_summary_rows,
)


def test_data_pack_diff_reports_roster_rank_and_pick_changes(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline"
    candidate = tmp_path / "candidate"
    _write_pack(
        baseline,
        roster_rows=[
            _roster("p1", "Alpha Back", "niners", "Niners", "10"),
            _roster("p2", "Beta Receiver", "niners", "Niners", "20"),
            _roster("p3", "Gamma Tight", "owls", "Owls", "30"),
        ],
        pick_owner_id="niners",
        pick_owner_name="Niners",
    )
    _write_pack(
        candidate,
        roster_rows=[
            _roster("p1", "Alpha Back", "niners", "Niners", "12"),
            _roster("p2", "Beta Receiver", "owls", "Owls", "20"),
            _roster("p4", "Delta Runner", "niners", "Niners", "40"),
        ],
        pick_owner_id="owls",
        pick_owner_name="Owls",
    )

    report = build_data_pack_diff_report(
        baseline_data_pack=baseline,
        candidate_data_pack=candidate,
    )

    assert len(report.roster_added) == 1
    assert len(report.roster_removed) == 1
    assert len(report.roster_moved) == 1
    assert len(report.league_rank_changed) == 1
    assert len(report.pick_owner_changed) == 1
    assert {row["change_type"] for row in diff_summary_rows(report)} == {
        "roster_added",
        "roster_removed",
        "roster_moved",
        "league_rank_changed",
        "pick_owner_changed",
    }
    detail_types = {row["change_type"] for row in diff_detail_rows(report)}
    assert "pick_owner_changed" in detail_types
    assert "league_rank_changed" in detail_types


def test_data_pack_diff_treats_league_rank_as_primary_rank(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline"
    candidate = tmp_path / "candidate"
    _write_pack(
        baseline,
        roster_rows=[_roster("p1", "Alpha Back", "niners", "Niners", "10")],
        ranking_uses_league_rank=True,
    )
    _write_pack(
        candidate,
        roster_rows=[_roster("p1", "Alpha Back", "niners", "Niners", "10")],
        ranking_uses_league_rank=True,
    )

    report = build_data_pack_diff_report(
        baseline_data_pack=baseline,
        candidate_data_pack=candidate,
    )

    assert report.league_rank_changed == ()


def _write_pack(
    path: Path,
    *,
    roster_rows: list[dict[str, str]],
    pick_owner_id: str = "niners",
    pick_owner_name: str = "Niners",
    ranking_uses_league_rank: bool = False,
) -> None:
    path.mkdir(parents=True)
    for file_name in REQUIRED_V1_FILES:
        schema = CSV_SCHEMAS[file_name]
        rows = _rows_for_file(
            file_name,
            roster_rows=roster_rows,
            pick_owner_id=pick_owner_id,
            pick_owner_name=pick_owner_name,
            ranking_uses_league_rank=ranking_uses_league_rank,
        )
        with (path / file_name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(schema.all_columns))
            writer.writeheader()
            writer.writerows(rows)


def _rows_for_file(
    file_name: str,
    *,
    roster_rows: list[dict[str, str]],
    pick_owner_id: str,
    pick_owner_name: str,
    ranking_uses_league_rank: bool,
) -> list[dict[str, object]]:
    if file_name == "dim_players.csv":
        return [
            {
                "player_id": row["player_id"],
                "player_name": row["player_name"],
                "position": row["position"],
                "active_flag": "1",
            }
            for row in roster_rows
        ]
    if file_name == "fact_rosters.csv":
        return roster_rows
    if file_name == "fact_official_rankings.csv":
        return [
            _ranking(row, use_league_rank=ranking_uses_league_rank)
            for row in roster_rows
        ]
    if file_name == "fact_future_picks.csv":
        return [
            {
                "snapshot_date": "2026-pre-draft",
                "season": "2026",
                "pick_year": "2026",
                "round": "1",
                "slot": "1",
                "pick_label": "2026 1.01",
                "current_team_id": pick_owner_id,
                "current_team_name": pick_owner_name,
            }
        ]
    if file_name == "fact_pick_values.csv":
        return [
            {
                "snapshot_date": "2026-pre-draft",
                "pick_year": "2026",
                "pick_label": "2026 1.01",
                "round": "1",
                "slot": "1",
                "overall_pick": "1",
                "base_value_1000": "1000",
                "final_pick_value": "1000",
            }
        ]
    if file_name == "model_outputs.csv":
        return [
            {
                "snapshot_date": "2026-pre-draft",
                "player_id": row["player_id"],
                "player_name": row["player_name"],
            }
            for row in roster_rows
        ]
    return [
        {
            "snapshot_date": "2026-pre-draft",
            "data_pack_name": "pack",
            "file_name": file_name,
        }
    ]


def _roster(
    player_id: str,
    player_name: str,
    team_id: str,
    team_name: str,
    league_rank: str,
) -> dict[str, str]:
    return {
        "snapshot_date": "2026-pre-draft",
        "season": "2026",
        "team_id": team_id,
        "team_name": team_name,
        "player_id": player_id,
        "player_name": player_name,
        "position": "RB",
        "league_rank": league_rank,
        "official_rank": league_rank,
    }


def _ranking(row: dict[str, str], *, use_league_rank: bool) -> dict[str, str]:
    rank_key = "league_rank" if use_league_rank else "official_rank"
    return {
        "snapshot_date": "2026-pre-draft",
        "season": "2026",
        "player_id": row["player_id"],
        "player_name": row["player_name"],
        rank_key: row["league_rank"],
    }
