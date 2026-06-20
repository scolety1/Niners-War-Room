from src.trading_lab.trade_lab_component import BEST_TRADE_CARD_LABELS
from src.trading_lab.trade_lab_ui import best_trade_package, packages_for_mode


def test_best_trade_card_includes_all_required_labels() -> None:
    for expected in (
        "Give",
        "Get",
        "NWR value gain",
        "Public fantasy market fairness",
        "Opponent fit",
        "Roster impact",
        "Risk flags",
        "Manual review verdict",
    ):
        assert expected in BEST_TRADE_CARD_LABELS


def test_give_get_labels_exist() -> None:
    package = best_trade_package(packages_for_mode("Trade For Player"))

    assert package.give
    assert package.get


def test_nwr_and_public_market_values_are_separate() -> None:
    package = best_trade_package(packages_for_mode("Trade For Player"))

    assert package.nwr_gain != 0
    assert package.public_market_fairness
    assert package.public_market_fairness != str(package.nwr_gain)


def test_fixture_only_caveat_exists() -> None:
    assert "Fixture-only caveat" in BEST_TRADE_CARD_LABELS


def test_no_automatic_recommendation_or_submit_language() -> None:
    text = " ".join(BEST_TRADE_CARD_LABELS).lower()

    for blocked in ("auto-submit", "submit trade", "execute trade", "automatic recommendation"):
        assert blocked not in text
