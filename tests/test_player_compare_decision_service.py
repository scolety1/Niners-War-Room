from __future__ import annotations

from src.services.player_compare_decision_service import (
    MARKET_DISPLAY_ONLY_NOTE,
    MULTI_PLAYER_COMPARE_NOTE,
    NFLVERSE_WAIT_STATUS,
    NOT_ENOUGH_INFORMATION,
    build_player_compare_decision_summary,
    decision_summary_rows,
    nflverse_spec_panel_rows,
)


def _player(name: str, **overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "player": name,
        "position": "WR",
        "dynasty_asset_rank": "",
        "cross_asset_candidate_rank": "",
        "final_board_rank": "",
        "age": "25.0",
        "candidate_value_band": "Strong review target",
        "confidence_band": "Medium",
        "outcome_applicable_summary": NOT_ENOUGH_INFORMATION,
        "available_pool_adp_range": NOT_ENOUGH_INFORMATION,
    }
    row.update(overrides)
    return row


def test_rank_gap_creates_visible_board_context_not_recommendation() -> None:
    summary = build_player_compare_decision_summary(
        _player("Zay Flowers", dynasty_asset_rank="1", age="25.8"),
        _player("Rookie WR", dynasty_asset_rank="20", age="22.0"),
    )

    assert summary.visible_context_read == "Visible board context differs"
    assert summary.lean == "Visible board context differs"
    assert "Prefer" not in summary.visible_context_read
    assert "Visible fields:" in summary.evidence_coverage
    assert any("Read-only board ranks" in reason for reason in summary.context_bullets)


def test_close_ranks_are_too_close_from_visible_context() -> None:
    summary = build_player_compare_decision_summary(
        _player("Zay Flowers", dynasty_asset_rank="1"),
        _player("Chris Olave", dynasty_asset_rank="2"),
    )

    assert summary.visible_context_read == "Too close to call from visible context"
    assert "High" not in summary.evidence_coverage
    assert "Medium" not in summary.evidence_coverage


def test_cross_position_compare_never_creates_preference() -> None:
    summary = build_player_compare_decision_summary(
        _player("WR Player", position="WR", dynasty_asset_rank="1"),
        _player("RB Player", position="RB", dynasty_asset_rank="25"),
    )

    assert summary.visible_context_read == "Different positions / roster-fit decision"
    assert any(
        "Different positions are not converted into a single player preference" in reason
        for reason in summary.context_bullets
    )


def test_market_data_alone_cannot_change_readout_or_review_flags() -> None:
    summary = build_player_compare_decision_summary(
        _player("Player Alpha", available_pool_adp_range="Early 1st equivalent"),
        _player("Player Beta", available_pool_adp_range="Depth / later"),
    )

    assert summary.visible_context_read == NOT_ENOUGH_INFORMATION
    assert summary.display_only_market_note == MARKET_DISPLAY_ONLY_NOTE
    assert not any("market" in flag.lower() for flag in summary.open_review_flags)


def test_multi_player_compare_keeps_review_context_note() -> None:
    summary = build_player_compare_decision_summary(
        _player("Player A", dynasty_asset_rank="1"),
        _player("Player B", dynasty_asset_rank="10"),
        [_player("Player C", dynasty_asset_rank="20")],
    )

    assert summary.multi_player_note == MULTI_PLAYER_COMPARE_NOTE
    assert "final ranking" in summary.context_note
    assert "recommendation" in summary.multi_player_note


def test_decision_summary_rows_preserve_input_order_and_remove_market_column() -> None:
    rows = decision_summary_rows(
        [
            _player("Player B", dynasty_asset_rank="20", available_pool_adp_range="Late"),
            _player("Player A", dynasty_asset_rank="1", available_pool_adp_range="Early"),
        ]
    )

    assert [row["Player"] for row in rows] == ["Player B", "Player A"]
    assert "Market / ADP Sanity" not in rows[0]
    assert rows[0]["Read-only board context"].startswith("NWR/Dynasty Candidate Rank")


def test_nflverse_spec_panels_are_waiting_for_refresh_health_green() -> None:
    rows = nflverse_spec_panel_rows()

    assert rows
    assert {row["Status"] for row in rows} == {NFLVERSE_WAIT_STATUS}
    assert {row["Safe to wire now"] for row in rows} == {"No"}
