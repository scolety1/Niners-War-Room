from src.trading_lab.trade_lab_fixtures import asset_by_name, team_context_by_name
from src.trading_lab.trade_scoring import (
    build_package_score,
    build_review_verdict,
    calculate_nwr_delta,
    calculate_public_market_delta,
)
from src.trading_lab.trade_value_contracts import TradePackage, TradeSide


def package_for(give: tuple[str, ...], get: tuple[str, ...]) -> TradePackage:
    return TradePackage(
        package_id="fake-score-package",
        mode="Trade For Player",
        give_side=TradeSide(
            team_name="NWR",
            assets=tuple(asset_by_name(name) for name in give),
        ),
        get_side=TradeSide(
            team_name="Team Alpha",
            assets=tuple(asset_by_name(name) for name in get),
        ),
        opponent_context=team_context_by_name("Team Alpha"),
    )


def test_nwr_delta_calculation_works_on_fake_values() -> None:
    package = package_for(("Player A", "2026 3rd"), ("Target Player",))

    assert calculate_nwr_delta(package) == 24.0


def test_market_fairness_uses_public_value_separately() -> None:
    package = package_for(("Player A", "2026 3rd"), ("Target Player",))
    score = build_package_score(package)

    assert calculate_public_market_delta(package) == 12.0
    assert score.nwr_delta == 24.0
    assert score.public_market_delta == 12.0
    assert score.nwr_delta != score.public_market_delta


def test_verdict_labels_match_expected_fake_package() -> None:
    package = package_for(("Player A", "2026 2nd"), ("Target Player",))
    score = build_package_score(package)

    assert score.market_fairness == "market-fair"
    assert build_review_verdict(score) == "review: strong fake package"


def test_negative_nwr_delta_can_still_be_market_fair() -> None:
    package = package_for(("Player B",), ("Player C", "2026 2nd"))
    score = build_package_score(package)

    assert score.nwr_delta > 0
    reverse = package_for(("Player C", "2026 2nd"), ("Player B",))
    reverse_score = build_package_score(reverse)
    assert reverse_score.public_market_delta <= 0


def test_positive_nwr_delta_can_be_flagged_unrealistic() -> None:
    package = package_for(("Player D",), ("Target Player",))
    score = build_package_score(package)

    assert score.nwr_delta > 0
    assert score.market_fairness == "unrealistic ask"
    assert build_review_verdict(score) == "hold: market realism concern"


def test_no_automated_submission_language_in_scoring_outputs() -> None:
    package = package_for(("Player A",), ("Player C",))
    text = repr(build_package_score(package)).lower()

    for blocked in ("auto-submit", "submit trade", "send offer", "execute"):
        assert blocked not in text
