from __future__ import annotations

from dataclasses import dataclass

from src.trading_lab.trade_lab_ui import DemoTradePackage, packages_for_mode


@dataclass(frozen=True)
class TradeForOfferBoard:
    cheapest_plausible_opener: DemoTradePackage
    fair_offer: DemoTradePackage
    aggressive_offer: DemoTradePackage
    max_offer: str
    player_only_offer: str
    pick_heavy_offer: str
    do_not_include_assets: tuple[str, ...]
    sweetener_suggestions: tuple[str, ...]


def build_trade_for_offer_board(
    packages: tuple[DemoTradePackage, ...] | None = None,
) -> TradeForOfferBoard:
    candidates = packages or packages_for_mode("Trade For Player")
    cheapest = min(candidates, key=lambda package: package.nwr_gain)
    fair = min(candidates, key=lambda package: abs(package.nwr_gain - 10))
    aggressive = max(candidates, key=lambda package: package.nwr_gain)
    player_only = next(
        (
            " + ".join(package.give)
            for package in candidates
            if all("Player" in item for item in package.give)
        ),
        "No player-only fixture offer",
    )
    pick_heavy = next(
        (
            " + ".join(package.give)
            for package in candidates
            if any("2026" in item for item in package.give)
        ),
        "No pick-heavy fixture offer",
    )
    return TradeForOfferBoard(
        cheapest_plausible_opener=cheapest,
        fair_offer=fair,
        aggressive_offer=aggressive,
        max_offer=aggressive.negotiation_ladder.max_offer,
        player_only_offer=player_only,
        pick_heavy_offer=pick_heavy,
        do_not_include_assets=aggressive.negotiation_ladder.do_not_include,
        sweetener_suggestions=("2026 3rd", "bench player swap", "remove protected asset"),
    )


def trade_for_offer_board_labels() -> tuple[str, ...]:
    return (
        "Cheapest plausible opener",
        "Fair offer",
        "Aggressive offer",
        "Max offer",
        "Player-only offer",
        "Pick-heavy offer",
        "Do-not-include assets",
        "Sweetener suggestions",
    )
