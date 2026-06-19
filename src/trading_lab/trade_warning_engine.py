from __future__ import annotations

from src.trading_lab.trade_lab_ui import TradeWarning
from src.trading_lab.trade_value_contracts import TradeReview


def detect_negative_nwr_edge(review: TradeReview) -> TradeWarning | None:
    if review.score.nwr_delta < 0 and review.score.market_fairness == "market-fair":
        return TradeWarning(
            "Market fair but NWR negative",
            "walk-away",
            "Public fantasy value looks fair, but fixture NWR value is negative.",
        )
    return None


def detect_unrealistic_market_gap(review: TradeReview) -> TradeWarning | None:
    if review.score.nwr_delta > 0 and review.score.market_fairness == "unrealistic ask":
        return TradeWarning(
            "NWR positive but unrealistic",
            "caution",
            "Fixture NWR value is positive, but public fantasy value gap is too large.",
        )
    return None


def detect_keeper_damage(review: TradeReview) -> TradeWarning | None:
    if any(asset.keeper_status == "core" for asset in review.package.give_side.assets):
        return TradeWarning(
            "Hurts keeper structure",
            "caution",
            "Package includes a core keeper from the outgoing side.",
        )
    return None


def detect_drop_pressure_damage(review: TradeReview) -> TradeWarning | None:
    if any(asset.drop_pressure_tag == "high" for asset in review.package.get_side.assets):
        return TradeWarning(
            "Worse drop pressure",
            "review",
            "Incoming asset adds high fixture drop pressure.",
        )
    return None


def detect_low_opponent_fit(review: TradeReview) -> TradeWarning | None:
    if review.score.opponent_fit == "low opponent fit":
        return TradeWarning(
            "Opponent has no reason to accept",
            "review",
            "Fixture opponent context does not show a clear roster need.",
        )
    return None


def detect_public_market_missing(review: TradeReview) -> TradeWarning | None:
    assets = (*review.package.give_side.assets, *review.package.get_side.assets)
    if any(asset.public_market_value <= 0 for asset in assets):
        return TradeWarning(
            "Public fantasy market source missing/stale",
            "review",
            "One fixture asset has no public fantasy market value.",
        )
    return None


def detect_untouchable_asset_included(
    review: TradeReview,
    untouchable_assets: tuple[str, ...] = ("Player B",),
) -> TradeWarning | None:
    outgoing = {asset.display_name for asset in review.package.give_side.assets}
    protected = outgoing.intersection(untouchable_assets)
    if protected:
        return TradeWarning(
            "Includes untouchable player",
            "walk-away",
            f"Outgoing side includes protected fixture asset: {', '.join(sorted(protected))}.",
        )
    return None


def build_trade_warnings(
    review: TradeReview,
    untouchable_assets: tuple[str, ...] = ("Player B",),
) -> tuple[TradeWarning, ...]:
    checks = (
        detect_negative_nwr_edge(review),
        detect_unrealistic_market_gap(review),
        detect_keeper_damage(review),
        detect_drop_pressure_damage(review),
        detect_low_opponent_fit(review),
        detect_public_market_missing(review),
        detect_untouchable_asset_included(review, untouchable_assets),
    )
    return tuple(warning for warning in checks if warning is not None)
