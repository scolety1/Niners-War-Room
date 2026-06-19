from src.trading_lab.trade_away_board import (
    build_trade_away_target_board,
    trade_away_target_board_labels,
)


def test_trade_away_target_board_builds_from_fixture_data() -> None:
    board = build_trade_away_target_board()

    assert board.best_nwr_return.mode == "Trade Away Player"
    assert board.most_realistic_return.mode == "Trade Away Player"


def test_return_categories_exist() -> None:
    labels = trade_away_target_board_labels()

    assert "Best NWR return" in labels
    assert "Most realistic return" in labels
    assert "Best win-now return" in labels
    assert "Best long-term return" in labels
    assert "Pick-heavy return" in labels
    assert "Player-heavy return" in labels


def test_do_not_accept_below_line_exists() -> None:
    board = build_trade_away_target_board()

    assert "Do not accept below" in board.do_not_accept_below
    assert "manual" not in board.do_not_accept_below.lower()


def test_target_board_remains_fantasy_football_oriented() -> None:
    text = repr(build_trade_away_target_board()).lower()

    assert "player" in text
    assert "2026" in text
    for blocked in ("stock", "broker", "crypto", "equity"):
        assert blocked not in text


def test_no_automatic_decisioning() -> None:
    text = repr(build_trade_away_target_board()).lower()

    for blocked in ("automatic decision", "auto-submit", "submit trade", "send offer"):
        assert blocked not in text
