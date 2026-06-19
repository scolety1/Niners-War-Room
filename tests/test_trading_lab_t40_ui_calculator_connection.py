from src.trading_lab.trade_lab_component import UNWIRED_INTEGRATION_NOTICE
from src.trading_lab.trade_lab_ui import (
    best_trade_package,
    format_negotiation_ladder,
    generate_fake_trade_packages,
    packages_for_mode,
)


def test_ui_helper_returns_scored_fixture_backed_packages() -> None:
    packages = generate_fake_trade_packages("Trade For Player")

    assert packages
    assert packages[0].nwr_gain
    assert packages[0].public_market_fairness in {
        "market-fair",
        "unrealistic ask",
        "favorable to opponent",
    }


def test_selected_mode_affects_package_output() -> None:
    trade_for = packages_for_mode("Trade For Player")
    trade_away = packages_for_mode("Trade Away Player")

    assert trade_for
    assert trade_away
    assert trade_for != trade_away
    assert {package.mode for package in trade_away} == {"Trade Away Player"}


def test_best_trade_card_comes_from_scoring_output() -> None:
    best = best_trade_package(packages_for_mode("Trade For Player"))

    assert best.nwr_gain == max(
        package.nwr_gain for package in packages_for_mode("Trade For Player")
    )
    assert best.verdict.startswith(("review:", "hold:"))


def test_negotiation_ladder_comes_from_helper() -> None:
    package = best_trade_package(packages_for_mode("Trade For Player"))
    ladder_lines = format_negotiation_ladder(package.negotiation_ladder)

    assert any("Opening offer" in line for line in ladder_lines)
    assert any("Walk-away line" in line for line in ladder_lines)


def test_roster_aftermath_comes_from_helper() -> None:
    package = best_trade_package(packages_for_mode("Drop-Pressure Trade"))

    assert "Fixture aftermath" in package.roster_aftermath.summary
    assert "not wired" in package.roster_aftermath.needs_real_integration_note


def test_warnings_come_from_helper() -> None:
    package = best_trade_package(packages_for_mode("Trade For Player"))

    assert package.warnings


def test_placeholder_labels_still_say_real_integrations_not_wired() -> None:
    assert "not wired yet" in UNWIRED_INTEGRATION_NOTICE
