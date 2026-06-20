from src.trading_lab.trade_lab_component import FAKE_DATA_DISCLAIMER, trade_lab_label_text
from src.trading_lab.trade_lab_ui import (
    TRADE_LAB_FIRST_SCREEN_HELP_TEXT,
    TRADE_LAB_REVIEW_QUESTIONS,
    TRADE_LAB_SUBTITLE,
    TRADE_LAB_TITLE,
)


def test_header_copy_includes_fantasy_trade_value_purpose() -> None:
    text = trade_lab_label_text()

    assert TRADE_LAB_TITLE == "Trade Lab"
    assert "fantasy trades" in TRADE_LAB_SUBTITLE
    assert "NWR edge" in TRADE_LAB_FIRST_SCREEN_HELP_TEXT
    assert all(question in text for question in TRADE_LAB_REVIEW_QUESTIONS)


def test_fake_fixture_status_is_visible() -> None:
    assert "Fixture-only review build" in FAKE_DATA_DISCLAIMER
    assert "fake in-memory" in FAKE_DATA_DISCLAIMER
    assert "not wired yet" in FAKE_DATA_DISCLAIMER


def test_manual_review_required_is_visible() -> None:
    assert "Manual review required" in trade_lab_label_text()


def test_no_old_wall_street_or_product_finance_wording() -> None:
    text = trade_lab_label_text().lower()

    for blocked in ("stock", "broker", "crypto", "equity", "order execution"):
        assert blocked not in text
