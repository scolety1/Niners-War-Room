from src.trading_lab.trade_lab_ui import (
    FAKE_DEMO_NAMES,
    PROHIBITED_DEMO_TERMS,
    generate_fake_trade_packages,
    sort_packages_by_review_score,
)


def test_generator_returns_multiple_packages() -> None:
    packages = generate_fake_trade_packages()

    assert len(packages) >= 4


def test_modes_produce_different_packages() -> None:
    trade_for = generate_fake_trade_packages("Trade For Player")
    trade_away = generate_fake_trade_packages("Trade Away Player")
    pick_conversion = generate_fake_trade_packages("Pick Conversion")

    assert trade_for
    assert trade_away
    assert pick_conversion
    assert trade_for != trade_away


def test_packages_include_required_review_fields() -> None:
    package = generate_fake_trade_packages()[0]

    assert package.give
    assert package.get
    assert package.nwr_gain
    assert package.public_market_fairness
    assert package.opponent_fit
    assert package.roster_impact


def test_package_sorting_prefers_higher_nwr_gain() -> None:
    sorted_packages = sort_packages_by_review_score(generate_fake_trade_packages())

    assert sorted_packages[0].nwr_gain >= sorted_packages[-1].nwr_gain


def test_fake_names_only_are_used() -> None:
    text = " ".join(
        " ".join((*package.give, *package.get, package.opponent_fit))
        for package in generate_fake_trade_packages()
    )

    assert "Player D" in text
    assert "Team Charlie" in text
    assert any(name in text for name in FAKE_DEMO_NAMES)


def test_no_real_data_file_paths_or_api_behavior() -> None:
    text = " ".join(repr(package) for package in generate_fake_trade_packages()).lower()

    for blocked in ("data/", "local_exports", ".csv", ".json", "fetch", "import real"):
        assert blocked not in text


def test_no_old_domain_language_in_fake_packages() -> None:
    text = " ".join(repr(package) for package in generate_fake_trade_packages()).lower()

    for term in PROHIBITED_DEMO_TERMS:
        assert term not in text
