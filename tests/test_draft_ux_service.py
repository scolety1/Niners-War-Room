from __future__ import annotations

import shutil
from pathlib import Path

from src.services.draft_state_service import (
    available_players_after_picks,
    best_option_rows_at_pick,
    best_remaining_by_position,
    create_empty_draft_state,
    mark_player_drafted,
)
from src.services.draft_ux_service import (
    DRAFT_ROUNDS,
    DRAFT_TEAMS,
    DRAFT_TOTAL_PICKS,
    RANKINGS_COLUMN_LABELS,
    RANKINGS_TABLE_COLUMNS,
    build_draft_ux_contract,
    build_rankings_table,
    draft_ux_summary_row,
    filter_rankings_rows,
)


def _real_pool_pack(tmp_path: Path) -> Path:
    source = Path("sample_data/2026_pre_declaration")
    pack = tmp_path / "real_pool_pack"
    shutil.copytree(source, pack)
    (pack / "fact_rookie_draftables.csv").write_text(
        "\n".join(
            [
                (
                    "player_id,player_name,position,nfl_team,why_available,"
                    "draft_value,market_value,confidence,pick_equivalent,"
                    "recommendation,recommended_range,do_not_draft_before_pick"
                ),
                (
                    "rookie_alpha,Alpha Rookie WR,WR,NYG,Current-year rookie "
                    "pool entrant.,91,84,88,1.04,rookie_target,1.04-1.06,4"
                ),
                (
                    "rookie_bellcow,Bellcow Rookie RB,RB,LV,Current-year rookie "
                    "pool entrant.,87,82,84,1.08,rookie_target,1.08-2.01,8"
                ),
                (
                    "p_lamar,Protected Rookie Error,QB,BAL,Should be excluded "
                    "because rostered.,99,99,99,1.01,rookie_target,1.01-1.01,1"
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (pack / "fact_available_veterans.csv").write_text(
        "\n".join(
            [
                (
                    "player_id,player_name,position,nfl_team,asset_type,"
                    "why_available,draft_value,market_value,confidence,"
                    "pick_equivalent,recommendation,recommended_range,"
                    "do_not_draft_before_pick"
                ),
                (
                    "released_wr,Released Veteran WR,WR,FA,released_veteran,"
                    "Declared released veteran.,76,73,79,2.05,available_veteran,"
                    "2.05-3.01,15"
                ),
                (
                    "free_te,Free Agent TE,TE,FA,free_agent,Available free agent.,"
                    "62,59,70,4.01,available_veteran,4.01-4.06,31"
                ),
                (
                    "p_chase_brown,Protected Veteran Error,RB,CIN,released_veteran,"
                    "Should be excluded because rostered.,98,98,98,1.01,"
                    "available_veteran,1.01-1.01,1"
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return pack


def test_draft_ux_contract_defines_two_clean_pages() -> None:
    contract = build_draft_ux_contract("sample_data/2026_pre_declaration")
    summary = draft_ux_summary_row(contract)

    assert [row["page"] for row in contract.page_rows] == ["Rankings", "Draft Board"]
    assert summary["visible_pages"] == "Rankings|Draft Board"
    assert summary["draft_shape"] == f"{DRAFT_ROUNDS} rounds x {DRAFT_TEAMS} teams"
    assert summary["total_picks"] == DRAFT_TOTAL_PICKS
    assert summary["status"] == "needs_data"
    assert "full rookie" in str(summary["next_phase"])
    assert summary["required_sources_total"] == 3
    assert summary["required_sources_ready"] < summary["required_sources_total"]
    assert all(
        "Old mixed-board" in row["must_not_show"]
        or "Raw source" in row["must_not_show"]
        for row in contract.page_rows
    )


def test_draft_ux_contract_builds_fifty_pick_grid() -> None:
    contract = build_draft_ux_contract("sample_data/2026_pre_declaration")

    assert len(contract.pick_grid_rows) == 50
    assert contract.pick_grid_rows[0]["overall_pick"] == 1
    assert contract.pick_grid_rows[0]["round"] == 1
    assert contract.pick_grid_rows[0]["round_pick"] == 1
    assert contract.pick_grid_rows[-1]["overall_pick"] == 50
    assert contract.pick_grid_rows[-1]["round"] == 5
    assert contract.pick_grid_rows[-1]["round_pick"] == 10


def test_draft_ux_contract_exposes_my_picks_and_available_pool() -> None:
    contract = build_draft_ux_contract("sample_data/2026_pre_declaration")

    assert contract.issues == [
        "No combined rookie/veteran available pool rows were detected."
    ]
    assert len(contract.my_pick_rows) >= 1
    assert {row["pool"] for row in contract.available_pool_rows} == {
        "rookies",
        "released veterans/free agents",
        "manual draftables",
        "combined available board",
    }
    assert {row["source"] for row in contract.available_pool_source_rows} == {
        "rookies",
        "released veterans",
        "free agents",
        "manual draftables",
    }
    assert not any(int(row["count"]) > 0 for row in contract.available_pool_rows)
    assert contract.best_option_rows == [
        {
            "pick": "",
            "player": "",
            "position": "",
            "asset_type": "",
            "draft_value": "",
            "reach_label": "",
            "logic": "needs my current-year picks and non-empty available pool",
        }
    ]


def test_missing_explicit_pool_does_not_fall_back_to_demo_or_unified_rows() -> None:
    contract = build_draft_ux_contract("sample_data/2026_pre_declaration")
    table = build_rankings_table("sample_data/2026_pre_declaration", review_only=True)
    summary = draft_ux_summary_row(contract)

    assert table.rows == []
    assert summary["available_pool_rows"] == 0
    assert summary["status"] == "needs_data"
    assert any("no rookies" in warning for warning in contract.available_pool_warnings)
    assert any("no released veterans" in warning for warning in contract.available_pool_warnings)
    assert any("no free agents" in warning for warning in contract.available_pool_warnings)


def test_rankings_table_uses_explicit_real_pool_and_excludes_protected_players(
    tmp_path: Path,
) -> None:
    pack = _real_pool_pack(tmp_path)
    table = build_rankings_table(pack, review_only=True)

    players = [str(row["player"]) for row in table.rows]

    assert players == [
        "Alpha Rookie WR",
        "Bellcow Rookie RB",
        "Released Veteran WR",
        "Free Agent TE",
    ]
    assert "Protected Rookie Error" not in players
    assert "Protected Veteran Error" not in players
    assert {row["asset_type"] for row in table.rows} == {
        "rookie",
        "released veteran",
        "free agent",
    }
    assert {row["why_available"] for row in table.rows} >= {
        "Current-year rookie pool entrant.",
        "Declared released veteran.",
        "Available free agent.",
    }


def test_rankings_table_uses_draft_focused_labels_and_default_sort(tmp_path: Path) -> None:
    table = build_rankings_table(_real_pool_pack(tmp_path), review_only=True)

    assert table.review_only is True
    assert table.default_sort == "stats_model_value"
    assert table.default_sort_direction == "desc"
    assert [RANKINGS_COLUMN_LABELS[column] for column in RANKINGS_TABLE_COLUMNS] == [
        "Rank",
        "Player",
        "Position",
        "NFL Team",
        "Asset Type",
        "Lifecycle",
        "Model Value",
        "Trade Market",
        "Model vs Market",
        "Confidence",
        "Confidence Label",
        "Warning",
        "Why Available",
    ]
    assert table.rows[0]["overall_rank"] == 1
    assert table.rows[0]["stats_model_value"] >= table.rows[1]["stats_model_value"]
    assert table.rows[0]["market_value"] == 84
    assert table.rows[0]["confidence_label"] == "strong"
    assert table.rows[0]["warning"] == "Review-only: calibration not passed"


def test_draft_surfaces_use_war_board_value_language() -> None:
    rankings_page = Path("app/pages/05_rankings.py").read_text()
    draft_board_page = Path("app/pages/06_draft_board.py").read_text()

    assert "Model Value is stats-first private value; Trade Market is liquidity only." in (
        draft_board_page
    )
    assert "Model Value {option.stats_model_value:.1f}" in draft_board_page
    assert "Trade Market {option.market_value:.1f}" in draft_board_page
    assert "Model vs Market {option.market_edge:+.1f}" in draft_board_page
    assert "Sorted by Stats Value" not in rankings_page
    assert "Stats/Model Value" not in draft_board_page


def test_draft_surfaces_keep_source_details_advanced() -> None:
    rankings_page = Path("app/pages/05_rankings.py").read_text()
    draft_board_page = Path("app/pages/06_draft_board.py").read_text()

    assert 'with st.expander("Advanced Filters", expanded=False):' in rankings_page
    assert '"Search Player"' in rankings_page
    assert '"Advanced: draft pool sources"' not in rankings_page
    assert '"Advanced: feature receipts"' in rankings_page
    assert '"Draft pool sources"' not in rankings_page

    assert '"Player Search"' in draft_board_page
    assert '"Rookie Analyzer"' in draft_board_page
    assert '"Pick Decision Lab"' in draft_board_page
    assert '"Prospect Board"' in draft_board_page
    assert '"Scout / Research"' in draft_board_page
    assert '"Receipts / Warnings"' in draft_board_page
    assert '"Draft pool incomplete. Mock mode works; live draft needs pool review."' in (
        draft_board_page
    )
    assert '"Pool readiness details"' in draft_board_page
    assert '"Advanced: current option receipts"' in draft_board_page
    assert '"Advanced: state and source details"' in draft_board_page
    assert '"Draft Pool Warning Details"' not in draft_board_page


def test_rankings_table_filters_by_position_asset_status_confidence_and_search(
    tmp_path: Path,
) -> None:
    table = build_rankings_table(_real_pool_pack(tmp_path), review_only=True)
    rows = filter_rankings_rows(
        table.rows,
        positions={"WR"},
        asset_types={"rookie"},
        lifecycles={"Incoming Rookie"},
        statuses={"available"},
        warnings={"Review-only: calibration not passed"},
        min_confidence=80,
        search="alpha",
    )

    assert [row["player"] for row in rows] == ["Alpha Rookie WR"]
    assert rows[0]["position"] == "WR"
    assert rows[0]["asset_type"] == "rookie"
    assert rows[0]["asset_lifecycle"] == "incoming_rookie"
    assert rows[0]["asset_lifecycle_label"] == "Incoming Rookie"
    assert rows[0]["why_available"] == "Current-year rookie pool entrant."
    assert rows[0]["draft_status"] == "available"
    assert rows[0]["warning"] == "Review-only: calibration not passed"


def test_rankings_table_supports_drafted_status_filter(tmp_path: Path) -> None:
    pack = _real_pool_pack(tmp_path)
    first_table = build_rankings_table(pack)
    drafted_id = str(first_table.rows[0]["asset_id"])

    table = build_rankings_table(
        pack,
        drafted_asset_ids={drafted_id},
    )
    drafted_rows = filter_rankings_rows(table.rows, statuses={"drafted"})

    assert [row["asset_id"] for row in drafted_rows] == [drafted_id]
    assert drafted_rows[0]["warning"] == "Already drafted in this mock"


def test_draft_board_state_uses_same_real_pool_as_rankings_and_removes_drafted_player(
    tmp_path: Path,
) -> None:
    pack = _real_pool_pack(tmp_path)
    contract = build_draft_ux_contract(pack)
    rankings = build_rankings_table(pack)
    state = create_empty_draft_state(
        pick_rows=contract.pick_grid_rows,
        available_rows=rankings.rows,
    )

    assert [row.asset_id for row in available_players_after_picks(state)] == [
        str(row["asset_id"]) for row in rankings.rows
    ]

    state = mark_player_drafted(state, "rookie:rookie_alpha")

    remaining_ids = [row.asset_id for row in available_players_after_picks(state)]
    assert "rookie:rookie_alpha" not in remaining_ids
    assert best_option_rows_at_pick(state, overall_pick=state.current_pick)[0].player == (
        "Bellcow Rookie RB"
    )
    assert best_option_rows_at_pick(state, overall_pick=state.current_pick)[
        0
    ].market_value == 82


def test_draft_board_best_remaining_by_position_comes_from_actual_draftable_pool(
    tmp_path: Path,
) -> None:
    pack = _real_pool_pack(tmp_path)
    rankings = build_rankings_table(pack)
    state = create_empty_draft_state(available_rows=rankings.rows)

    rows = best_remaining_by_position(state, limit_per_position=1)

    assert [(row.position, row.player) for row in rows] == [
        ("RB", "Bellcow Rookie RB"),
        ("WR", "Alpha Rookie WR"),
        ("TE", "Free Agent TE"),
    ]
