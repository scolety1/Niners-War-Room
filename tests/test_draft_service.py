from __future__ import annotations

from pathlib import Path

from pytest import MonkeyPatch

import src.services.draft_service as draft_service
from src.data.validators import ValidatedDataPack
from src.services.draft_service import build_draft_room

SAMPLE_PACK = "sample_data/2026_pre_declaration"


def test_draft_room_joins_future_picks_to_snapshot_values() -> None:
    board = build_draft_room(SAMPLE_PACK)

    assert board.snapshot_date == "2026-08-01"
    assert board.teams == ["Niners"]
    assert board.certainties == ["known", "projected"]
    assert board.pick_rows[0] == {
        "pick": "2026 1.04",
        "current_team": "Niners",
        "original_team": "Niners",
        "pick_year": 2026,
        "round": 1,
        "overall_pick": 4,
        "certainty": "known",
        "base_value": 630.0,
        "snapshot_value": 630.0,
        "future_discount": 1.0,
        "certainty_factor": 1.0,
        "bucket": "round-1",
    }


def test_draft_room_team_totals_use_snapshot_values() -> None:
    board = build_draft_room(SAMPLE_PACK)

    assert board.team_rows == [
        {
            "team": "Niners",
            "picks": 3,
            "snapshot_value": 1283.6,
            "highest_pick": "2026 1.04",
        }
    ]


def test_draft_room_includes_rookies_in_mixed_combined_board(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    rows_by_table = _draft_rows_by_table()
    _write_explicit_draft_pool(
        tmp_path,
        rookie_line=(
            "rookie_wr,Rookie Alpha,WR,DAL,Current rookie board,90,84,91,"
            "1.04,target,1.04-1.08,4"
        ),
        released_line=(
            "released_rb,Released RB,RB,FA,released_veteran,Declared release,"
            "78,72,85,2.04,target,2.01-2.06,14"
        ),
    )
    monkeypatch.setattr(
        draft_service,
        "validate_data_pack",
        lambda path: ValidatedDataPack(
            data_pack_path=Path(str(path)),
            data_pack_name="draft-room-test",
            snapshot_date="2026-08-01",
            rows_by_table=rows_by_table,
            issues=(),
        ),
    )
    monkeypatch.setattr(
        draft_service,
        "build_unified_asset_board",
        lambda *args, **kwargs: _FakeAssetBoard([]),
    )
    monkeypatch.setattr(
        draft_service,
        "build_forced_release_strategy",
        lambda path: _FakeReleaseStrategy(),
    )

    board = build_draft_room(tmp_path)

    assert [row["player"] for row in board.rookie_rows] == ["Rookie Alpha"]
    assert [row["player"] for row in board.released_veteran_rows] == [
        "Released RB",
        "Available Free Agent",
    ]
    assert "Rostered Hold" not in {row["player"] for row in board.combined_rows}


def test_draft_room_combined_board_sorts_rookies_against_available_veterans(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    rows_by_table = _draft_rows_by_table()
    _write_explicit_draft_pool(
        tmp_path,
        rookie_line=(
            "rookie_wr,Rookie Alpha,WR,DAL,Current rookie board,88,84,91,"
            "1.04,target,1.04-1.08,4"
        ),
        released_line=(
            "released_rb,Released RB,RB,FA,released_veteran,Declared release,"
            "92,70,85,1.04,target,1.04-1.08,4"
        ),
    )
    monkeypatch.setattr(
        draft_service,
        "validate_data_pack",
        lambda path: ValidatedDataPack(
            data_pack_path=Path(str(path)),
            data_pack_name="draft-room-test",
            snapshot_date="2026-08-01",
            rows_by_table=rows_by_table,
            issues=(),
        ),
    )
    monkeypatch.setattr(
        draft_service,
        "build_unified_asset_board",
        lambda *args, **kwargs: _FakeAssetBoard([]),
    )
    monkeypatch.setattr(
        draft_service,
        "build_forced_release_strategy",
        lambda path: _FakeReleaseStrategy(),
    )

    board = build_draft_room(tmp_path)

    assert [row["player"] for row in board.combined_rows] == [
        "Released RB",
        "Rookie Alpha",
        "Available Free Agent",
    ]
    assert board.best_available_rows[0]["pick"] == "2026 1.04"
    assert board.best_available_rows[0]["player"] == "Released RB"
    assert board.best_available_rows[0]["reach_label"] in {"Value", "Fair"}


def test_draft_room_includes_manual_draftables_but_not_protected_roster_players(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    rows_by_table = _draft_rows_by_table()
    rows_by_table["rosters"] = [
        {
            "snapshot_date": "2026-08-01",
            "season": 2026,
            "team_id": "other",
            "team_name": "Other",
            "player_id": "p_protected",
            "player_name": "Protected Star",
            "position": "WR",
            "roster_status": "rostered",
        }
    ]
    (tmp_path / "fact_manual_draftables.csv").write_text(
        "\n".join(
            [
                (
                    "player_id,player_name,position,nfl_team,manual_status,"
                    "why_available,draft_value,market_value,confidence"
                ),
                "p_manual,Manual Sleeper,RB,FA,,Manual commissioner add,70,65,80",
                "p_protected,Protected Star,WR,MIN,,Should not leak,99,99,90",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        draft_service,
        "validate_data_pack",
        lambda path: ValidatedDataPack(
            data_pack_path=Path(str(path)),
            data_pack_name="draft-room-test",
            snapshot_date="2026-08-01",
            rows_by_table=rows_by_table,
            issues=(),
        ),
    )
    monkeypatch.setattr(
        draft_service,
        "build_unified_asset_board",
        lambda *args, **kwargs: _FakeAssetBoard(
            [_asset_row("rookie:wr", "rookie", "Rookie Alpha", "WR", 88, 84)]
        ),
    )
    monkeypatch.setattr(
        draft_service,
        "build_forced_release_strategy",
        lambda path: _FakeReleaseStrategy(),
    )

    board = build_draft_room(tmp_path)

    assert [row["player"] for row in board.manual_draftable_rows] == ["Manual Sleeper"]
    assert "Protected Star" not in {row["player"] for row in board.combined_rows}
    assert board.manual_draftable_rows[0]["asset_type_label"] == "manual"
    assert board.manual_draftable_rows[0]["why_available"] == "Manual commissioner add"


def test_draft_room_reads_explicit_rookie_and_available_veteran_sources(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    rows_by_table = _draft_rows_by_table()
    _write_explicit_draft_pool(tmp_path)
    monkeypatch.setattr(
        draft_service,
        "validate_data_pack",
        lambda path: ValidatedDataPack(
            data_pack_path=Path(str(path)),
            data_pack_name="draft-room-test",
            snapshot_date="2026-08-01",
            rows_by_table=rows_by_table,
            issues=(),
        ),
    )
    monkeypatch.setattr(
        draft_service,
        "build_unified_asset_board",
        lambda *args, **kwargs: _FakeAssetBoard([]),
    )
    monkeypatch.setattr(
        draft_service,
        "build_forced_release_strategy",
        lambda path: _FakeReleaseStrategy(),
    )

    board = build_draft_room(tmp_path)

    assert [row["player"] for row in board.rookie_rows] == ["Real Rookie"]
    assert [row["player"] for row in board.released_veteran_rows] == [
        "Released Veteran",
        "Available Free Agent",
    ]
    source_status = {row["source"]: row["status"] for row in board.available_pool_source_rows}
    assert source_status["rookies"] == "loaded"
    assert source_status["released veterans"] == "loaded"
    assert source_status["free agents"] == "loaded"
    assert board.available_pool_warnings == []


def test_explicit_draft_pool_excludes_protected_players_unless_manual(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    rows_by_table = _draft_rows_by_table()
    rows_by_table["rosters"] = [
        {
            "snapshot_date": "2026-08-01",
            "season": 2026,
            "team_id": "other",
            "team_name": "Other",
            "player_id": "p_protected",
            "player_name": "Protected Star",
            "position": "WR",
            "roster_status": "rostered",
        }
    ]
    _write_explicit_draft_pool(
        tmp_path,
        rookie_line=(
            "p_protected,Protected Star,WR,MIN,Should not leak,99,99,90,"
            "1.01,target,1.01-1.03,1"
        ),
        released_line=(
            "p_protected,Protected Star,WR,MIN,released_veteran,Should not leak,"
            "99,99,90,1.01,target,1.01-1.03,1"
        ),
    )
    (tmp_path / "fact_manual_draftables.csv").write_text(
        "\n".join(
            [
                (
                    "player_id,player_name,position,nfl_team,manual_status,"
                    "why_available,draft_value,market_value,confidence"
                ),
                "p_protected,Protected Star,WR,MIN,include,Explicit room add,70,65,80",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        draft_service,
        "validate_data_pack",
        lambda path: ValidatedDataPack(
            data_pack_path=Path(str(path)),
            data_pack_name="draft-room-test",
            snapshot_date="2026-08-01",
            rows_by_table=rows_by_table,
            issues=(),
        ),
    )
    monkeypatch.setattr(
        draft_service,
        "build_unified_asset_board",
        lambda *args, **kwargs: _FakeAssetBoard([]),
    )
    monkeypatch.setattr(
        draft_service,
        "build_forced_release_strategy",
        lambda path: _FakeReleaseStrategy(),
    )

    board = build_draft_room(tmp_path)

    assert board.rookie_rows == []
    assert "Protected Star" not in {row["player"] for row in board.released_veteran_rows}
    assert [row["player"] for row in board.manual_draftable_rows] == ["Protected Star"]
    assert "Protected Star" in {
        row["player"] for row in board.combined_rows if row["asset_type"] == "manual"
    }


def test_draft_room_manual_include_can_override_protected_roster_status(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    rows_by_table = _draft_rows_by_table()
    rows_by_table["rosters"] = [
        {
            "snapshot_date": "2026-08-01",
            "season": 2026,
            "team_id": "other",
            "team_name": "Other",
            "player_id": "p_protected",
            "player_name": "Protected Star",
            "position": "WR",
            "roster_status": "rostered",
        }
    ]
    (tmp_path / "fact_manual_draftables.csv").write_text(
        "\n".join(
            [
                (
                    "player_id,player_name,position,nfl_team,manual_status,"
                    "why_available,draft_value,market_value,confidence"
                ),
                "p_protected,Protected Star,WR,MIN,include,Explicit override,72,70,75",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        draft_service,
        "validate_data_pack",
        lambda path: ValidatedDataPack(
            data_pack_path=Path(str(path)),
            data_pack_name="draft-room-test",
            snapshot_date="2026-08-01",
            rows_by_table=rows_by_table,
            issues=(),
        ),
    )
    monkeypatch.setattr(
        draft_service,
        "build_unified_asset_board",
        lambda *args, **kwargs: _FakeAssetBoard([]),
    )
    monkeypatch.setattr(
        draft_service,
        "build_forced_release_strategy",
        lambda path: _FakeReleaseStrategy(),
    )

    board = build_draft_room(tmp_path)

    assert [row["player"] for row in board.manual_draftable_rows] == ["Protected Star"]
    assert board.manual_draftable_rows[0]["why_available"] == "Explicit override"


def test_draft_room_available_pool_warns_when_veteran_side_is_missing() -> None:
    board = build_draft_room(SAMPLE_PACK)

    assert any(
        "no released veterans" in warning
        for warning in board.available_pool_warnings
    )
    assert any("no free agents" in warning for warning in board.available_pool_warnings)


def test_draft_room_warns_when_rookie_pool_is_missing() -> None:
    board = build_draft_room(SAMPLE_PACK)

    assert any(
        "no rookies" in warning for warning in board.available_pool_warnings
    )


class _FakeAssetBoard:
    def __init__(self, rows: list[dict[str, object]]) -> None:
        self.rows = rows
        self.asset_types = sorted({str(row["asset_type"]) for row in rows})
        self.positions = sorted({str(row["position"]) for row in rows})
        self.recommendations = sorted({str(row["recommendation"]) for row in rows})


class _FakeReleaseStrategy:
    draft_target_rows: list[dict[str, object]] = []


def _draft_rows_by_table() -> dict[str, list[dict[str, object]]]:
    return {
        "future_picks": [
            {
                "snapshot_date": "2026-08-01",
                "pick_year": 2026,
                "pick_label": "2026 1.04",
                "current_team_id": "niners",
                "current_team_name": "Niners",
                "original_team_id": "niners",
                "original_team_name": "Niners",
                "round": 1,
                "overall_pick": 4,
                "certainty": "known",
            }
        ],
        "pick_values": [
            {
                "snapshot_date": "2026-08-01",
                "pick_year": 2026,
                "pick_label": "2026 1.04",
                "round": 1,
                "slot": 4,
                "overall_pick": 4,
                "base_value_1000": 630,
                "final_pick_value": 630,
                "future_discount": 1.0,
                "certainty_adjustment": 1.0,
                "bucket": "round-1",
            }
        ],
        "rosters": [],
        "official_rankings": [],
        "model_outputs": [],
    }


def _asset_row(
    asset_id: str,
    asset_type: str,
    player: str,
    position: str,
    all_value: float,
    market_value: float,
) -> dict[str, object]:
    return {
        "asset_id": asset_id,
        "asset_type": asset_type,
        "player": player,
        "position": position,
        "team": "Pool",
        "all_asset_value": all_value,
        "acquisition_value": all_value,
        "keeper_adjusted_value": all_value,
        "trade_liquidity_value": market_value,
        "confidence": 90.0,
        "pick_equivalent": "1.01-1.03",
        "recommendation": "target",
        "source": "test",
    }


def _write_explicit_draft_pool(
    root: Path,
    *,
    rookie_line: str = (
        "rookie_1,Real Rookie,WR,DAL,Current rookie board,88,82,91,"
        "1.05,target,1.04-1.08,4"
    ),
    released_line: str = (
        "vet_1,Released Veteran,RB,FA,released_veteran,Declared release,"
        "76,70,85,2.04,target,2.01-2.06,14"
    ),
) -> None:
    (root / "fact_rookie_draftables.csv").write_text(
        "\n".join(
            [
                (
                    "player_id,player_name,position,nfl_team,why_available,draft_value,"
                    "market_value,confidence,pick_equivalent,recommendation,"
                    "recommended_range,do_not_draft_before_pick"
                ),
                rookie_line,
            ]
        ),
        encoding="utf-8",
    )
    (root / "fact_available_veterans.csv").write_text(
        "\n".join(
            [
                (
                    "player_id,player_name,position,nfl_team,asset_type,why_available,"
                    "draft_value,market_value,confidence,pick_equivalent,recommendation,"
                    "recommended_range,do_not_draft_before_pick"
                ),
                released_line,
                (
                    "fa_1,Available Free Agent,TE,FA,free_agent,Open free agent,"
                    "61,59,75,4.05,watch,4.01-4.10,35"
                ),
            ]
        ),
        encoding="utf-8",
    )
