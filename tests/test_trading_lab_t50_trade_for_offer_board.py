from src.trading_lab.trade_for_board import (
    build_trade_for_offer_board,
    trade_for_offer_board_labels,
)


def test_trade_for_offer_board_builds_from_fixture_data() -> None:
    board = build_trade_for_offer_board()

    assert board.cheapest_plausible_opener.mode == "Trade For Player"
    assert board.fair_offer.mode == "Trade For Player"
    assert board.aggressive_offer.mode == "Trade For Player"


def test_offer_categories_exist() -> None:
    labels = trade_for_offer_board_labels()

    assert "Cheapest plausible opener" in labels
    assert "Fair offer" in labels
    assert "Aggressive offer" in labels
    assert "Player-only offer" in labels
    assert "Pick-heavy offer" in labels


def test_max_offer_and_walkaway_context_exists() -> None:
    board = build_trade_for_offer_board()

    assert board.max_offer
    assert board.do_not_include_assets


def test_sweetener_suggestions_exist() -> None:
    board = build_trade_for_offer_board()

    assert board.sweetener_suggestions
    assert "2026 3rd" in board.sweetener_suggestions


def test_no_automated_send_or_submission_language() -> None:
    text = repr(build_trade_for_offer_board()).lower()

    for blocked in ("auto-submit", "send offer", "submit trade", "execute trade"):
        assert blocked not in text
