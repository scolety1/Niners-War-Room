from __future__ import annotations

import csv
import json
from pathlib import Path

from src.services.nflverse_player_context_display_service import (
    NEED_DATASET_REFRESH,
    NEED_IDENTITY_REVIEW,
    SAFE_NOW_DISPLAY_ONLY,
    build_nflverse_player_context_display,
    write_nflverse_player_context_display_docs,
)


def test_player_context_artifact_loads_with_required_guardrails(tmp_path: Path) -> None:
    snapshot = _snapshot_with_context_rows(tmp_path)
    output_dir = tmp_path / "docs"

    result = write_nflverse_player_context_display_docs(
        output_dir=output_dir,
        shared_root=tmp_path / "shared",
        status_root=tmp_path / "status",
        snapshot_dir=snapshot,
        rankings_rows=[_ranking_row()],
    )

    artifact = _read_csv(output_dir / "nflverse_player_context_display_artifact.csv")
    schema = _read_csv(output_dir / "nflverse_player_context_schema_manifest.csv")
    join_health = _read_csv(output_dir / "nflverse_player_context_join_health.csv")

    assert result.verdict == "YELLOW_PARTIAL_PLAYER_CONTEXT_ARTIFACT"
    assert artifact[0]["identity_join_status"] == SAFE_NOW_DISPLAY_ONLY
    assert artifact[0]["nflverse_gsis_id"] == "00-0039150"
    assert artifact[0]["weekly_roster_status"] == "ACT"
    assert artifact[0]["injury_report_status"] == "Questionable"
    assert artifact[0]["injury_report_date_week"].startswith("season=2025; week=2")
    assert artifact[0]["practice_status"] == "Limited Participation in Practice"
    assert artifact[0]["depth_chart_position"] == "QB"
    assert artifact[0]["depth_chart_rank"] == "1"
    assert artifact[0]["depth_chart_role"] == "formation=Offense; depth_team=1; pos_group=QB"
    assert artifact[0]["snap_count_recency"] == "season=2025; week=2"
    assert artifact[0]["snap_sample_size"] == "1"
    assert artifact[0]["last_active_season"] == "2025"
    assert artifact[0]["last_active_week"] == "2"
    assert artifact[0]["draft_round"] == "1"
    assert artifact[0]["draft_pick"] == "3"
    assert artifact[0]["contract_context"] == "active=True; team=NE; year_signed=2025; years=4"
    assert _join_gate(join_health, "current_rankings_identity_gate")["clean_join_rows"] == "1"
    assert {row["model_use_allowed"] for row in artifact} == {"false"}
    assert {row["training_allowed"] for row in artifact} == {"false"}
    assert {row["source_truth_allowed"] for row in artifact} == {"false"}
    assert {row["rank_logic_allowed"] for row in artifact} == {"false"}
    assert {row["hidden_sort_allowed"] for row in artifact} == {"false"}
    assert {row["trade_value_allowed"] for row in artifact} == {"false"}
    assert {row["pick_value_allowed"] for row in artifact} == {"false"}
    assert {row["display_only"] for row in artifact} == {"true"}
    assert {row["model_use_allowed"] for row in schema} == {"false"}


def test_missing_fields_are_not_clean_or_zero_defaults(tmp_path: Path) -> None:
    snapshot = _snapshot_with_context_rows(
        tmp_path,
        include_snap=False,
        include_injury=False,
        include_depth=False,
        include_draft=False,
    )

    result = build_nflverse_player_context_display(
        shared_root=tmp_path / "shared",
        status_root=tmp_path / "status",
        snapshot_dir=snapshot,
        rankings_rows=[_ranking_row()],
    )

    row = result.artifact_rows[0]
    combined = ",".join(row.values()).lower()
    assert row["snap_count_recency"] == "Not enough information"
    assert row["snap_sample_size"] == "Not enough information"
    assert row["injury_report_status"] == NEED_DATASET_REFRESH
    assert row["depth_chart_role"] == NEED_DATASET_REFRESH
    assert row["draft_round"] == NEED_DATASET_REFRESH
    assert "injury_missing_nei" in row["notes"]
    assert "depth_chart_missing_nei" in row["notes"]
    assert "zero snaps" not in combined
    assert "confirmed udfa" not in combined
    assert "round 8" not in combined


def test_ambiguous_identity_remains_review_needed(tmp_path: Path) -> None:
    snapshot = _snapshot_with_context_rows(tmp_path, duplicate_sleeper=True)

    result = build_nflverse_player_context_display(
        shared_root=tmp_path / "shared",
        status_root=tmp_path / "status",
        snapshot_dir=snapshot,
        rankings_rows=[_ranking_row()],
    )

    row = result.artifact_rows[0]
    assert row["identity_join_status"] == NEED_IDENTITY_REVIEW
    assert row["identity_caveat"] == "one_nwr_player_id_maps_to_multiple_gsis_ids"
    assert row["nflverse_gsis_id"] == "Not enough information"
    assert row["review_required"] == "true"


def test_ff_rankings_is_blocked_and_not_used(tmp_path: Path) -> None:
    snapshot = _snapshot_with_context_rows(tmp_path)

    result = build_nflverse_player_context_display(
        shared_root=tmp_path / "shared",
        status_root=tmp_path / "status",
        snapshot_dir=snapshot,
        rankings_rows=[_ranking_row()],
    )

    ff_gate = _join_gate(result.join_health_rows, "ff_rankings_source_policy_gate")
    assert ff_gate["status"] == "BLOCKED_VENDOR_OR_PRIVATE"
    assert ff_gate["blocked_rows"] == "1"
    assert "ff_rankings" not in ",".join(result.artifact_rows[0].values()).lower()


def _snapshot_with_context_rows(
    tmp_path: Path,
    *,
    duplicate_sleeper: bool = False,
    include_snap: bool = True,
    include_injury: bool = True,
    include_depth: bool = True,
    include_draft: bool = True,
) -> Path:
    snapshot = tmp_path / "shared" / "scheduled_ingest" / "nflverse" / "run"
    snapshot.mkdir(parents=True)
    roster_rows = [
        {
            "season": "2025",
            "week": "2",
            "team": "NE",
            "position": "QB",
            "status": "ACT",
            "full_name": "Drake Maye",
            "birth_date": "2002-08-30",
            "gsis_id": "00-0039150",
            "sleeper_id": "11566",
        }
    ]
    if duplicate_sleeper:
        roster_rows.append(
            {
                "season": "2025",
                "week": "2",
                "team": "NE",
                "position": "QB",
                "status": "ACT",
                "full_name": "Drake Maybe",
                "birth_date": "2002-08-30",
                "gsis_id": "00-0099999",
                "sleeper_id": "11566",
            }
        )
    _write_csv(snapshot / "rosters.csv", roster_rows)
    _write_csv(snapshot / "weekly_rosters.csv", roster_rows)
    _write_csv(
        snapshot / "players.csv",
        [
            {
                "gsis_id": "00-0039150",
                "display_name": "Drake Maye",
                "full_name": "Drake Maye",
                "pfr_id": "MayeDr00",
                "espn_id": "4431452",
                "birth_date": "2002-08-30",
                "position": "QB",
                "latest_team": "NE",
                "status": "ACT",
            }
        ],
    )
    _write_csv(
        snapshot / "ff_playerids.csv",
        [
            {
                "gsis_id": "00-0039150",
                "sleeper_id": "11566",
                "espn_id": "4431452",
                "pfr_id": "MayeDr00",
                "name": "Drake Maye",
                "player_name": "Drake Maye",
                "position": "QB",
                "team": "NE",
                "birthdate": "2002-08-30",
            }
        ],
    )
    if include_snap:
        _write_csv(
            snapshot / "snap_counts.csv",
            [
                {
                    "game_id": "2025_02_NE_NYJ",
                    "season": "2025",
                    "week": "2",
                    "player": "Drake Maye",
                    "position": "QB",
                    "team": "NE",
                    "offense_snaps": "63",
                    "offense_pct": "1.0",
                }
            ],
        )
    if include_injury:
        _write_csv(
            snapshot / "injuries.csv",
            [
                {
                    "season": "2025",
                    "week": "2",
                    "team": "NE",
                    "gsis_id": "00-0039150",
                    "position": "QB",
                    "full_name": "Drake Maye",
                    "player_name": "Drake Maye",
                    "status": "Questionable",
                    "injury": "Knee",
                    "report_status": "Questionable",
                    "practice_status": "Limited Participation in Practice",
                    "date_modified": "2025-09-12 12:00:00+00:00",
                }
            ],
        )
    if include_depth:
        _write_csv(
            snapshot / "depth_charts.csv",
            [
                {
                    "season": "2025",
                    "week": "2",
                    "team": "NE",
                    "club_code": "NE",
                    "depth_team": "1",
                    "position": "QB",
                    "depth_position": "QB",
                    "player_name": "Drake Maye",
                    "full_name": "Drake Maye",
                    "formation": "Offense",
                    "pos_grp": "QB",
                    "pos_rank": "1",
                    "gsis_id": "00-0039150",
                }
            ],
        )
    if include_draft:
        _write_csv(
            snapshot / "draft_picks.csv",
            [
                {
                    "season": "2024",
                    "draft_year": "2024",
                    "round": "1",
                    "pick": "3",
                    "team": "NE",
                    "player_name": "Drake Maye",
                    "gsis_id": "00-0039150",
                }
            ],
        )
    _write_csv(
        snapshot / "contracts.csv",
        [
            {
                "player": "Drake Maye",
                "player_name": "Drake Maye",
                "position": "QB",
                "team": "NE",
                "is_active": "True",
                "year_signed": "2025",
                "years": "4",
                "contract_years": "4",
                "gsis_id": "00-0039150",
            }
        ],
    )
    _write_csv(
        snapshot / "schedules.csv",
        [
            {
                "game_id": "2025_02_NE_NYJ",
                "season": "2025",
                "week": "2",
                "home_team": "NE",
                "away_team": "NYJ",
                "game_type": "REG",
            }
        ],
    )
    _write_csv(
        snapshot / "weekly_stats.csv",
        [
            {
                "player_id": "00-0039150",
                "player_name": "D.Maye",
                "player_display_name": "Drake Maye",
                "position": "QB",
                "recent_team": "NE",
                "season": "2025",
                "week": "2",
            }
        ],
    )
    datasets = [
        _metadata_row(
            "players",
            "players.csv",
            ["gsis_id", "display_name", "full_name", "pfr_id", "espn_id"],
            1,
        ),
        _metadata_row(
            "rosters",
            "rosters.csv",
            ["season", "team", "position", "gsis_id", "full_name", "sleeper_id"],
            len(roster_rows),
        ),
        _metadata_row(
            "weekly_rosters",
            "weekly_rosters.csv",
            ["season", "week", "team", "position", "gsis_id", "full_name", "sleeper_id"],
            len(roster_rows),
        ),
        _metadata_row(
            "ff_playerids",
            "ff_playerids.csv",
            ["gsis_id", "sleeper_id", "espn_id", "pfr_id", "name", "player_name"],
            1,
        ),
        _metadata_row(
            "schedules",
            "schedules.csv",
            ["season", "week", "game_id", "home_team", "away_team", "game_type"],
            1,
        ),
        _metadata_row(
            "player_stats_weekly",
            "weekly_stats.csv",
            ["season", "week", "player_id", "player_name", "player_display_name"],
            1,
        ),
    ]
    if include_snap:
        datasets.append(
            _metadata_row(
                "snap_counts",
                "snap_counts.csv",
                ["season", "week", "player", "position", "team", "offense_snaps"],
                1,
            )
        )
    if include_injury:
        datasets.append(
            _metadata_row(
                "injuries",
                "injuries.csv",
                ["season", "week", "team", "player_name", "status", "report_status", "injury"],
                1,
            )
        )
    if include_depth:
        datasets.append(
            _metadata_row(
                "depth_charts",
                "depth_charts.csv",
                [
                    "season",
                    "week",
                    "team",
                    "club_code",
                    "depth_team",
                    "position",
                    "depth_position",
                    "player_name",
                ],
                1,
            )
        )
    if include_draft:
        datasets.append(
            _metadata_row(
                "draft_picks",
                "draft_picks.csv",
                ["season", "draft_year", "round", "pick", "team", "player_name", "gsis_id"],
                1,
            )
        )
    datasets.append(
        _metadata_row(
            "contracts",
            "contracts.csv",
            ["player", "player_name", "team", "year_signed", "contract_years"],
            1,
        )
    )
    (snapshot / "snapshot_metadata.json").write_text(
        json.dumps(
            {
                "created_at": "2026-06-30T12:00:00+00:00",
                "package_version": "test",
                "seasons": [2025],
                "datasets": datasets,
            }
        ),
        encoding="utf-8",
    )
    return snapshot


def _ranking_row() -> dict[str, str]:
    return {
        "player_id": "11566",
        "player_name": "Drake Maye",
        "position": "QB",
        "nfl_team": "NE",
        "source_coverage": "Full Dynasty source",
        "nwr_rank": "42",
        "final_board_rank": "",
    }


def _metadata_row(
    name: str, file_name: str, field_names: list[str], row_count: int
) -> dict[str, object]:
    return {
        "name": name,
        "file_name": file_name,
        "status": "ok",
        "row_count": row_count,
        "column_count": len(field_names),
        "field_names": field_names,
    }


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _join_gate(
    rows: list[dict[str, str]] | tuple[dict[str, str], ...],
    gate: str,
) -> dict[str, str]:
    return next(row for row in rows if row["gate"] == gate)
