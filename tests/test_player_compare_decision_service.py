from __future__ import annotations

from src.services.player_compare_decision_service import (
    MARKET_DISPLAY_ONLY_NOTE,
    NOT_ENOUGH_INFORMATION,
    build_player_compare_decision_summary,
    decision_summary_rows,
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
        "current_pick_value": NOT_ENOUGH_INFORMATION,
    }
    row.update(overrides)
    return row


def test_clear_rank_edge_creates_lean() -> None:
    summary = build_player_compare_decision_summary(
        _player("Zay Flowers", dynasty_asset_rank="1", age="25.8"),
        _player("Rookie WR", dynasty_asset_rank="20", age="22.0"),
    )

    assert summary.lean == "Prefer Zay Flowers"
    assert summary.confidence == "Medium"
    assert any("better NWR/Dynasty Candidate rank" in reason for reason in summary.reason_bullets)


def test_close_ranks_create_close_depends() -> None:
    summary = build_player_compare_decision_summary(
        _player("Zay Flowers", dynasty_asset_rank="1"),
        _player("Chris Olave", dynasty_asset_rank="2"),
    )

    assert summary.lean == "Close / depends on roster"
    assert summary.confidence == "Medium"


def test_missing_rank_data_is_low_confidence() -> None:
    summary = build_player_compare_decision_summary(
        _player("Unknown A", age=""),
        _player("Unknown B", available_pool_adp_range="Early 1st equivalent"),
    )

    assert summary.lean == NOT_ENOUGH_INFORMATION
    assert summary.confidence == "Low"
    assert summary.data_quality == "Low"


def test_market_data_alone_cannot_create_recommendation() -> None:
    summary = build_player_compare_decision_summary(
        _player("Market Darling", available_pool_adp_range="Early 1st equivalent"),
        _player("Market Fade", available_pool_adp_range="Depth / later"),
    )

    assert summary.lean == NOT_ENOUGH_INFORMATION
    assert summary.display_only_market_note == MARKET_DISPLAY_ONLY_NOTE


def test_injury_and_warning_context_appears_as_red_flag() -> None:
    summary = build_player_compare_decision_summary(
        _player(
            "Tyreek Hill",
            dynasty_asset_rank="18",
            age="32.3",
            confidence_band="Low",
            on_clock_warning="LOUD WARNING: major age/status risk.",
        ),
        _player("Younger WR", dynasty_asset_rank="30"),
    )

    assert summary.confidence == "Low"
    assert any("LOUD WARNING" in flag for flag in summary.red_flags)


def test_unsupported_outcome_is_not_treated_as_bad_outcome() -> None:
    summary = build_player_compare_decision_summary(
        _player(
            "Supported Player",
            dynasty_asset_rank="5",
            outcome_applicable_summary="WR T24=49%",
        ),
        _player(
            "Unsupported Player",
            dynasty_asset_rank="25",
            outcome_applicable_summary="unsupported",
        ),
    )

    assert summary.lean == "Prefer Supported Player"
    assert not any("bad outcome" in flag.lower() for flag in summary.red_flags)


def test_decision_summary_rows_include_market_display_only_context() -> None:
    rows = decision_summary_rows(
        [
            _player(
                "Player A",
                dynasty_asset_rank="1",
                available_pool_adp_range="Early 1st equivalent",
                current_pick_value="Value",
            )
        ]
    )

    assert rows[0]["Market / ADP Sanity"] == "Early 1st equivalent / Value"
