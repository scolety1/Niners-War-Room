from src.trading_lab.trade_lab_ui import (
    best_trade_package,
    format_negotiation_ladder,
    packages_for_mode,
)
from src.trading_lab.trade_negotiation import NEGOTIATION_POLISH_LABELS, NEGOTIATION_REVIEW_NOTE


def test_all_ladder_sections_exist() -> None:
    labels = " ".join(NEGOTIATION_POLISH_LABELS)

    for expected in (
        "Opener",
        "Fair offer",
        "Max offer",
        "Walk-away line",
        "Do-not-include assets",
        "Counteroffer ideas",
        "If they reject",
        "If they ask for more",
    ):
        assert expected in labels


def test_walkaway_and_do_not_include_assets_exist() -> None:
    package = best_trade_package(packages_for_mode("Trade For Player"))
    lines = format_negotiation_ladder(package.negotiation_ladder)

    assert any("Walk-away line" in line for line in lines)
    assert any("Do-not-include assets" in line for line in lines)


def test_manual_only_language_exists() -> None:
    assert "Manual fantasy negotiation guidance only" in NEGOTIATION_REVIEW_NOTE
    assert "fixture-only" in NEGOTIATION_REVIEW_NOTE


def test_no_send_submit_execute_language() -> None:
    text = " ".join((NEGOTIATION_REVIEW_NOTE, *NEGOTIATION_POLISH_LABELS)).lower()

    for blocked in ("send offer", "submit trade", "execute trade"):
        assert blocked not in text
