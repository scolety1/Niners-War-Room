from __future__ import annotations

from src.trading_lab.trade_lab_ui import NegotiationLadder
from src.trading_lab.trade_value_contracts import TradeReview


def _asset_names(review: TradeReview) -> tuple[str, ...]:
    return tuple(asset.display_name for asset in review.package.give_side.assets)


def build_opening_offer(review: TradeReview) -> str:
    give_names = _asset_names(review)
    if len(give_names) > 1:
        return " + ".join(give_names[:-1])
    return give_names[0] if give_names else "No opening offer"


def build_fair_offer(review: TradeReview) -> str:
    give_names = _asset_names(review)
    return " + ".join(give_names) if give_names else "No fair offer"


def build_max_offer(review: TradeReview) -> str:
    fair_offer = build_fair_offer(review)
    if review.score.nwr_delta >= 20:
        return f"{fair_offer} plus one small sweetener"
    return fair_offer


def build_walk_away_line(review: TradeReview) -> str:
    if review.score.nwr_delta < 0:
        return "Walk away from this package"
    core_assets = [
        asset.display_name
        for asset in review.package.give_side.assets
        if asset.keeper_status == "core"
    ]
    if core_assets:
        return f"Do not add beyond {', '.join(core_assets)}"
    return "Do not add a core keeper"


def build_counteroffer_notes(review: TradeReview) -> tuple[str, ...]:
    if review.score.market_fairness == "unrealistic ask":
        return ("Ask for a smaller fake package return or add only a low-value pick.",)
    if review.score.nwr_delta >= 10:
        return ("Start below fair value and preserve the max offer for later.",)
    return ("Compare against another fake package before increasing the offer.",)


def build_do_not_include_assets(review: TradeReview) -> tuple[str, ...]:
    protected = tuple(
        asset.display_name
        for asset in review.package.give_side.assets
        if asset.keeper_status == "core"
    )
    return protected or ("Core keeper",)


def build_negotiation_ladder(review: TradeReview) -> NegotiationLadder:
    return NegotiationLadder(
        opening_offer=build_opening_offer(review),
        fair_offer=build_fair_offer(review),
        max_offer=build_max_offer(review),
        walk_away=build_walk_away_line(review),
        do_not_include=build_do_not_include_assets(review),
        counteroffer_ideas=build_counteroffer_notes(review),
        if_reject="Ask which roster need matters most and compare another fake package.",
        if_ask_for_more="Move one step only if the fixture NWR delta stays positive.",
    )
