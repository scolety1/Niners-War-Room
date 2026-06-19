from dataclasses import replace

from src.trading_lab.trade_lab_fixtures import asset_by_name, team_context_by_name
from src.trading_lab.trade_scoring import build_trade_review
from src.trading_lab.trade_value_contracts import TradePackage, TradeSide
from src.trading_lab.trade_warning_engine import (
    build_trade_warnings,
    detect_drop_pressure_damage,
    detect_keeper_damage,
    detect_low_opponent_fit,
    detect_negative_nwr_edge,
    detect_public_market_missing,
    detect_unrealistic_market_gap,
    detect_untouchable_asset_included,
)


def package(give: tuple[str, ...], get: tuple[str, ...], team: str = "Team Alpha"):
    return TradePackage(
        package_id="warning-package",
        mode="Trade Review",
        give_side=TradeSide(
            team_name="NWR",
            assets=tuple(asset_by_name(name) for name in give),
        ),
        get_side=TradeSide(
            team_name=team,
            assets=tuple(asset_by_name(name) for name in get),
        ),
        opponent_context=team_context_by_name(team),
    )


def test_market_fair_but_nwr_negative_warning() -> None:
    review = build_trade_review(package(("Player B",), ("Player C", "2026 2nd")))
    forced = replace(
        review,
        score=replace(review.score, nwr_delta=-1.0, market_fairness="market-fair"),
    )

    assert detect_negative_nwr_edge(forced).label == "Market fair but NWR negative"


def test_nwr_positive_but_unrealistic_warning() -> None:
    review = build_trade_review(package(("Player D",), ("Target Player",)))

    assert detect_unrealistic_market_gap(review).label == "NWR positive but unrealistic"


def test_keeper_damage_warning() -> None:
    review = build_trade_review(package(("Player B",), ("Target Player",)))

    assert detect_keeper_damage(review).label == "Hurts keeper structure"


def test_drop_pressure_warning() -> None:
    review = build_trade_review(package(("2026 3rd",), ("Player D",)))

    assert detect_drop_pressure_damage(review).label == "Worse drop pressure"


def test_low_opponent_fit_warning() -> None:
    review = build_trade_review(package(("2026 3rd",), ("Player C",)))
    forced = replace(review, score=replace(review.score, opponent_fit="low opponent fit"))

    assert detect_low_opponent_fit(forced).label == "Opponent has no reason to accept"


def test_untouchable_asset_warning() -> None:
    review = build_trade_review(package(("Player B",), ("Target Player",)))

    assert detect_untouchable_asset_included(review).label == "Includes untouchable player"


def test_public_market_missing_warning() -> None:
    player = replace(asset_by_name("Player A"), public_market_value=0.0)
    review = build_trade_review(
        TradePackage(
            package_id="missing-public-value",
            mode="Trade Review",
            give_side=TradeSide(team_name="NWR", assets=(player,)),
            get_side=TradeSide(team_name="Team Alpha", assets=(asset_by_name("Player C"),)),
            opponent_context=team_context_by_name("Team Alpha"),
        )
    )

    assert (
        detect_public_market_missing(review).label
        == "Public fantasy market source missing/stale"
    )


def test_build_trade_warnings_has_no_old_wall_street_language() -> None:
    review = build_trade_review(package(("Player B",), ("Target Player",)))
    text = repr(build_trade_warnings(review)).lower()

    for blocked in ("stock", "broker", "crypto", "equity", "order execution"):
        assert blocked not in text
