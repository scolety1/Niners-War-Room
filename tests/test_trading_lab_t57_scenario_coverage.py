from src.trading_lab.trade_lab_component import SCENARIO_COVERAGE_LABELS
from src.trading_lab.trade_scenarios import build_trade_scenarios, scenario_titles

EXPECTED_SCENARIOS = {
    "Trade for elite player",
    "Trade away aging veteran",
    "Consolidate depth",
    "Pick conversion",
    "Drop pressure cleanup",
    "Opponent-fit package",
    "Market-fair but NWR-negative trap",
    "NWR-positive but unrealistic trap",
    "Keeper-damage trap",
    "All assets untouchable fallback",
}


def test_each_scenario_exists() -> None:
    assert set(scenario_titles()) == EXPECTED_SCENARIOS
    assert set(SCENARIO_COVERAGE_LABELS) == EXPECTED_SCENARIOS


def test_each_scenario_produces_reviewable_output() -> None:
    for scenario in build_trade_scenarios():
        assert scenario.title
        assert scenario.mode
        assert scenario.review_notes
        assert scenario.packages or "fallback" in scenario.scenario_id


def test_traps_produce_warnings() -> None:
    trap_scenarios = [
        scenario
        for scenario in build_trade_scenarios()
        if "trap" in scenario.scenario_id
    ]

    assert trap_scenarios
    assert all(scenario.expected_warnings for scenario in trap_scenarios)


def test_fallback_scenarios_do_not_crash() -> None:
    fallback = next(
        scenario
        for scenario in build_trade_scenarios()
        if scenario.scenario_id == "all-assets-untouchable-fallback"
    )

    assert fallback.packages == ()
    assert "No fixture-backed packages available" in " ".join(fallback.review_notes)


def test_no_real_integration_required() -> None:
    text = repr(build_trade_scenarios()).lower()

    for blocked in ("http", "fetch", "data/", "local_exports", "real integration is wired"):
        assert blocked not in text
