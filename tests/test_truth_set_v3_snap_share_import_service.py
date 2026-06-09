from __future__ import annotations

import csv
from pathlib import Path

from src.services.truth_set_v3_snap_share_import_service import (
    V3_SNAP_SEASON_HEADER,
    V3_SNAP_WEEK_HEADER,
    SnapPlayer,
    TruthSetV3SnapResult,
    aggregate_snap_season_rows,
    build_snap_week_rows_from_source_rows,
    write_truth_set_v3_snap_outputs,
)


def test_snap_share_import_maps_pfr_identity_and_labels_snap_share_only() -> None:
    rows = build_snap_week_rows_from_source_rows(
        [
            _snap_row(
                player="Receiver One",
                pfr_player_id="ReceOn00",
                position="WR",
                team="SEA",
                offense_snaps="61",
                offense_pct="89%",
            )
        ],
        players=[SnapPlayer("Receiver One", "Receiver One", "00-abc", "WR", "SEA")],
        identity_rows=[
            {
                "pfr_id": "ReceOn00",
                "gsis_id": "00-0031234",
                "sleeper_id": "9999",
                "review_status": "ready",
            }
        ],
        seasons={2024},
    )

    assert len(rows) == 1
    row = rows[0]
    assert row["player_id"] == "00-abc"
    assert row["gsis_id"] == "00-0031234"
    assert row["sleeper_id"] == "9999"
    assert row["offense_snaps"] == 61
    assert row["offense_pct"] == 0.89
    assert row["snap_share"] == 0.89
    assert row["game_with_offensive_snaps"] == 1
    assert row["source_status"] == "imported_real_data"
    assert row["identity_warning"] == ""
    assert "snap_share_only_not_route_participation" == row["notes"]


def test_snap_share_import_warns_when_pfr_id_is_not_in_identity_map() -> None:
    rows = build_snap_week_rows_from_source_rows(
        [_snap_row(player="Runner One", pfr_player_id="RunnOn00", position="RB", team="ATL")],
        players=[SnapPlayer("Runner One", "Runner One", "00-rb", "RB", "ATL")],
        identity_rows=[],
        seasons={2024},
    )

    assert rows[0]["match_method"] == "name_position_team_match"
    assert rows[0]["identity_warning"] == "pfr_id_not_in_identity_map"
    assert rows[0]["gsis_id"] == ""
    assert rows[0]["sleeper_id"] == ""


def test_snap_share_import_can_match_team_aliases_without_route_estimates() -> None:
    rows = build_snap_week_rows_from_source_rows(
        [_snap_row(player="Puka Nacua", pfr_player_id="NacuPu00", position="WR", team="LA")],
        players=[SnapPlayer("Puka Nacua", "Puka Nacua", "00-puka", "WR", "LAR")],
        identity_rows=[],
        seasons={2024},
    )

    assert rows[0]["player_id"] == "00-puka"
    assert rows[0]["match_method"] == "name_position_team_match"
    assert "route" in rows[0]["notes"]


def test_snap_season_aggregation_counts_games_and_average_snap_share() -> None:
    week_rows = build_snap_week_rows_from_source_rows(
        [
            _snap_row(
                player="Runner One",
                pfr_player_id="RunnOn00",
                position="RB",
                team="ATL",
                week="1",
                offense_snaps="40",
                offense_pct="0.5",
            ),
            _snap_row(
                player="Runner One",
                pfr_player_id="RunnOn00",
                position="RB",
                team="ATL",
                week="2",
                offense_snaps="60",
                offense_pct="0.75",
            ),
        ],
        players=[SnapPlayer("Runner One", "Runner One", "00-rb", "RB", "ATL")],
        seasons={2024},
    )

    season = aggregate_snap_season_rows(week_rows)[0]

    assert season["games"] == 2
    assert season["games_with_offensive_snaps"] == 2
    assert season["offense_snaps"] == 100
    assert season["avg_offense_pct"] == 0.625
    assert season["avg_snap_share"] == 0.625
    assert season["source_status"] == "imported_real_data"


def test_snap_write_uses_stable_headers(tmp_path: Path) -> None:
    rows = build_snap_week_rows_from_source_rows(
        [_snap_row(player="Receiver One", pfr_player_id="ReceOn00", position="WR", team="SEA")],
        players=[SnapPlayer("Receiver One", "Receiver One", "00-wr", "WR", "SEA")],
        seasons={2024},
    )
    result = TruthSetV3SnapResult(
        week_rows=tuple(rows),
        season_rows=tuple(aggregate_snap_season_rows(rows)),
        missing_rows=(),
        summary={"status": "ready"},
    )

    paths = write_truth_set_v3_snap_outputs(tmp_path, result)

    assert _header(paths["week"]) == V3_SNAP_WEEK_HEADER
    assert _header(paths["season"]) == V3_SNAP_SEASON_HEADER


def _snap_row(
    *,
    player: str,
    pfr_player_id: str,
    position: str,
    team: str,
    season: str = "2024",
    week: str = "1",
    offense_snaps: str = "50",
    offense_pct: str = "0.8",
) -> dict[str, str]:
    return {
        "game_id": f"{season}_{week}_TEST",
        "season": season,
        "game_type": "REG",
        "week": week,
        "player": player,
        "pfr_player_id": pfr_player_id,
        "position": position,
        "team": team,
        "opponent": "OPP",
        "offense_snaps": offense_snaps,
        "offense_pct": offense_pct,
        "st_snaps": "0",
        "st_pct": "0",
    }


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
