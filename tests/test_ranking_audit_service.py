from __future__ import annotations

from src.services.ranking_audit_service import (
    build_ranking_audit,
    ranking_audit_summary_rows,
)

SAMPLE_PACK = "sample_data/2026_pre_declaration"


def test_ranking_audit_covers_major_visible_boards() -> None:
    report = build_ranking_audit(SAMPLE_PACK)

    assert {
        "War Board",
        "My Team",
        "League Intel",
        "Draft Board",
        "Trade Lab",
    }.issubset(set(report.pages))
    assert report.rows
    assert ranking_audit_summary_rows(report)


def test_ranking_audit_rows_have_explicit_rank_sources() -> None:
    report = build_ranking_audit(SAMPLE_PACK)

    for row in report.rows:
        assert row["page"]
        assert row["source"]
        assert int(row["displayed_rank"]) >= 1
        assert row["rank_column"]
        assert row["rank_value"] is not None
        assert row["sort_direction"]


def test_ranking_audit_documents_war_board_sort_column() -> None:
    report = build_ranking_audit(SAMPLE_PACK)
    war_rows = [row for row in report.rows if str(row["source"]).startswith("war_board:")]

    assert war_rows
    assert {
        "war_board:pure_model_value",
        "war_board:keeper_decision",
        "war_board:trade_liquidity",
        "war_board:forced_release_pain",
    }.issubset({str(row["source"]) for row in war_rows})
    assert {row["surface"] for row in war_rows} >= {
        "Pure Model Value",
        "Keeper Decision",
        "Trade/Liquidity",
        "Forced-Release Pain",
    }
    pure_rows = [row for row in war_rows if row["source"] == "war_board:pure_model_value"]
    assert {row["rank_column"] for row in pure_rows} == {
        "stats_value/private_lve_value descending"
    }
    assert all(row["intended_use"] for row in war_rows)


def test_ranking_audit_exposes_my_team_roster_as_source_order() -> None:
    report = build_ranking_audit(SAMPLE_PACK)
    roster_rows = [row for row in report.rows if row["source"] == "roster_command_table"]

    assert roster_rows
    assert {row["rank_column"] for row in roster_rows} == {"source_roster_order"}
    assert {row["sort_direction"] for row in roster_rows} == {"source_order"}


def test_ranking_audit_documents_non_war_board_sort_columns() -> None:
    report = build_ranking_audit(SAMPLE_PACK)
    rows_by_source = {row["source"]: row for row in report.rows}

    assert rows_by_source["default_release_candidates"]["rank_column"] == (
        "acquisition_value"
    )
    assert rows_by_source["unified_asset_board"]["rank_column"] == "acquisition_value"
    assert rows_by_source["player_signals"]["rank_column"] == "signal_order,trade_value"
    assert rows_by_source["pick_paths"]["rank_column"] == "absolute_value_gap"
