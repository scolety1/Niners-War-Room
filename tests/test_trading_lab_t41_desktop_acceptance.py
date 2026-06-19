from src.trading_lab.trade_lab_component import UNWIRED_INTEGRATION_NOTICE
from src.trading_lab.trade_lab_ui import (
    best_trade_package,
    empty_state_message,
    format_negotiation_ladder,
    packages_for_mode,
    safe_packages_for_review,
    training_scenarios,
)


def assert_ranked_packages(mode: str) -> None:
    packages = packages_for_mode(mode)

    assert packages
    assert best_trade_package(packages).nwr_gain >= packages[-1].nwr_gain


def test_trade_for_flow_creates_ranked_packages() -> None:
    assert_ranked_packages("Trade For Player")


def test_trade_away_flow_creates_ranked_packages() -> None:
    assert_ranked_packages("Trade Away Player")


def test_upgrade_position_flow_creates_ranked_packages() -> None:
    assert_ranked_packages("Upgrade Position")


def test_pick_conversion_flow_creates_ranked_packages() -> None:
    assert_ranked_packages("Pick Conversion")


def test_drop_pressure_trade_flow_creates_ranked_packages() -> None:
    assert_ranked_packages("Drop-Pressure Trade")


def test_training_mode_still_has_fake_scenarios() -> None:
    scenarios = training_scenarios()

    assert len(scenarios) >= 3
    assert all("fake scenario" in scenario.disclaimer for scenario in scenarios)


def test_best_package_has_review_dimensions() -> None:
    package = best_trade_package(packages_for_mode("Trade For Player"))

    assert package.nwr_gain
    assert package.public_market_fairness
    assert package.opponent_fit
    assert package.roster_impact


def test_warnings_and_negotiation_ladder_render() -> None:
    package = best_trade_package(packages_for_mode("Trade For Player"))

    assert package.warnings
    assert format_negotiation_ladder(package.negotiation_ladder)


def test_no_real_integrations_claimed() -> None:
    assert "not wired yet" in UNWIRED_INTEGRATION_NOTICE


def test_missing_target_player_returns_empty_fallback() -> None:
    assert safe_packages_for_review("Trade For Player", target_player="") == ()


def test_missing_outgoing_player_returns_empty_fallback() -> None:
    assert safe_packages_for_review("Trade Away Player", outgoing_player="") == ()


def test_unsupported_mode_falls_back_to_trade_for() -> None:
    packages = safe_packages_for_review("Unsupported Mode")

    assert packages
    assert {package.mode for package in packages} == {"Trade For Player"}


def test_all_assets_untouchable_returns_empty_fallback() -> None:
    packages = safe_packages_for_review(
        "Trade For Player",
        untouchable_assets=("Player A", "Player B", "2026 2nd", "2026 3rd"),
    )

    assert packages == ()
    assert "No fixture-backed packages available" in empty_state_message("Trade For Player")
