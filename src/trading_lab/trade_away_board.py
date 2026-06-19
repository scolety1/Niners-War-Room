from __future__ import annotations

from dataclasses import dataclass

from src.trading_lab.trade_lab_ui import DemoTradePackage, packages_for_mode


@dataclass(frozen=True)
class TradeAwayTargetBoard:
    best_nwr_return: DemoTradePackage
    most_realistic_return: DemoTradePackage
    best_win_now_return: DemoTradePackage
    best_long_term_return: DemoTradePackage
    pick_heavy_return: DemoTradePackage
    player_heavy_return: DemoTradePackage
    do_not_accept_below: str


def _trade_away_packages() -> tuple[DemoTradePackage, ...]:
    return packages_for_mode("Trade Away Player")


def build_trade_away_target_board(
    packages: tuple[DemoTradePackage, ...] | None = None,
) -> TradeAwayTargetBoard:
    candidates = packages or _trade_away_packages()
    best_nwr = max(candidates, key=lambda package: package.nwr_gain)
    most_realistic = min(candidates, key=lambda package: abs(package.nwr_gain))
    pick_heavy = max(candidates, key=lambda package: sum("2026" in asset for asset in package.get))
    player_heavy = max(
        candidates,
        key=lambda package: sum("Player" in asset for asset in package.get),
    )
    long_term = pick_heavy
    win_now = player_heavy
    return TradeAwayTargetBoard(
        best_nwr_return=best_nwr,
        most_realistic_return=most_realistic,
        best_win_now_return=win_now,
        best_long_term_return=long_term,
        pick_heavy_return=pick_heavy,
        player_heavy_return=player_heavy,
        do_not_accept_below="Do not accept below a market-fair package with non-negative NWR gain.",
    )


def trade_away_target_board_labels() -> tuple[str, ...]:
    return (
        "Best NWR return",
        "Most realistic return",
        "Best win-now return",
        "Best long-term return",
        "Pick-heavy return",
        "Player-heavy return",
        "Do-not-accept-below line",
    )
