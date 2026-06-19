from src.trading_lab.trade_package_builder import (
    build_trade_away_candidates,
    build_trade_for_candidates,
    candidate_packages_for_mode,
    rank_candidate_packages,
)


def test_trade_for_returns_multiple_ranked_packages() -> None:
    reviews = rank_candidate_packages(build_trade_for_candidates())

    assert len(reviews) >= 2
    assert reviews[0].score.nwr_delta >= reviews[-1].score.nwr_delta


def test_trade_away_returns_multiple_ranked_packages() -> None:
    reviews = rank_candidate_packages(build_trade_away_candidates())

    assert len(reviews) >= 2
    assert all(review.package.mode == "Trade Away Player" for review in reviews)


def test_ranking_includes_nwr_market_and_opponent_fit() -> None:
    review = rank_candidate_packages(build_trade_for_candidates())[0]

    assert isinstance(review.score.nwr_delta, float)
    assert review.score.market_fairness
    assert review.score.opponent_fit


def test_package_includes_negotiation_ladder_placeholder_reference() -> None:
    package = build_trade_for_candidates()[0]

    assert "negotiation ladder placeholder" in package.notes


def test_candidate_packages_for_mode_uses_deterministic_fixture_values() -> None:
    first = candidate_packages_for_mode("Pick Conversion")
    second = candidate_packages_for_mode("Pick Conversion")

    assert first == second
    assert {package.mode for package in first} == {"Pick Conversion"}


def test_no_real_data_import_terms_in_candidate_repr() -> None:
    text = repr(candidate_packages_for_mode("Trade For Player")).lower()

    for blocked in ("data/", "local_exports", ".csv", ".json", "fetch", "http"):
        assert blocked not in text
