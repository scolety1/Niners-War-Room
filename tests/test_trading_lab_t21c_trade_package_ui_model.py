from src.trading_lab.trade_lab_ui import (
    PROHIBITED_DEMO_TERMS,
    bad_trade_warnings,
    best_trade_package,
    demo_payload_text,
    demo_trade_packages,
    format_package_summary,
)


def test_fake_package_objects_include_fantasy_trade_fields() -> None:
    package = demo_trade_packages()[0]

    assert package.mode == "Trade For Player"
    assert package.give
    assert package.get
    assert package.nwr_gain > 0
    assert package.public_market_fairness
    assert package.opponent_fit
    assert package.roster_impact
    assert package.keeper_drop_impact
    assert package.verdict


def test_negotiation_ladder_exists() -> None:
    ladder = demo_trade_packages()[0].negotiation_ladder

    assert ladder.opening_offer
    assert ladder.fair_offer
    assert ladder.max_offer
    assert ladder.walk_away


def test_roster_aftermath_exists() -> None:
    aftermath = demo_trade_packages()[0].roster_aftermath

    assert aftermath.summary
    assert aftermath.keeper_impact
    assert aftermath.drop_pressure_impact
    assert aftermath.positional_depth_impact
    assert aftermath.rookie_mock_context


def test_bad_trade_warnings_exist() -> None:
    package = demo_trade_packages()[1]

    assert bad_trade_warnings(package)


def test_best_package_and_summary_format() -> None:
    package = best_trade_package()
    summary = format_package_summary(package)

    assert "Give" in summary
    assert "NWR value" in summary


def test_no_old_domain_terms_in_labels_or_demo_payloads() -> None:
    text = demo_payload_text().lower()

    for term in PROHIBITED_DEMO_TERMS:
        assert term not in text


def test_no_real_data_paths_are_referenced() -> None:
    text = demo_payload_text().lower()

    assert "data/" not in text
    assert "local_exports" not in text
    assert ".csv" not in text
    assert ".json" not in text
