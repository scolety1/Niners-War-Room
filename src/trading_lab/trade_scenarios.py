from __future__ import annotations

from dataclasses import dataclass

from src.trading_lab.trade_lab_ui import (
    DemoTradePackage,
    empty_state_message,
    packages_for_mode,
    safe_packages_for_review,
)


@dataclass(frozen=True)
class TradeScenario:
    scenario_id: str
    title: str
    mode: str
    packages: tuple[DemoTradePackage, ...]
    review_notes: tuple[str, ...]
    expected_warnings: tuple[str, ...]


def build_trade_scenarios() -> tuple[TradeScenario, ...]:
    all_untouchable = safe_packages_for_review(
        "Trade For Player",
        untouchable_assets=("Player A", "Player B", "2026 2nd", "2026 3rd"),
    )
    return (
        TradeScenario(
            "trade-for-elite-player",
            "Trade for elite player",
            "Trade For Player",
            packages_for_mode("Trade For Player"),
            ("Review NWR gain and max offer.",),
            ("unrealistic",),
        ),
        TradeScenario(
            "trade-away-aging-veteran",
            "Trade away aging veteran",
            "Trade Away Player",
            packages_for_mode("Trade Away Player"),
            ("Compare return targets before lowering ask.",),
            ("manual review",),
        ),
        TradeScenario(
            "consolidate-depth",
            "Consolidate depth",
            "Consolidate Depth",
            packages_for_mode("Consolidate Depth"),
            ("Review depth loss against roster cleanup.",),
            ("keeper",),
        ),
        TradeScenario(
            "pick-conversion",
            "Pick conversion",
            "Pick Conversion",
            packages_for_mode("Pick Conversion"),
            ("Check whether pick spend fits roster timeline.",),
            ("market",),
        ),
        TradeScenario(
            "drop-pressure-cleanup",
            "Drop pressure cleanup",
            "Drop-Pressure Trade",
            packages_for_mode("Drop-Pressure Trade"),
            ("Confirm pressure improves without moving a core player.",),
            ("drop",),
        ),
        TradeScenario(
            "opponent-fit-package",
            "Opponent-fit package",
            "Opponent-Fit Trade",
            packages_for_mode("Opponent-Fit Trade"),
            ("Review whether opponent needs make the package plausible.",),
            ("opponent",),
        ),
        TradeScenario(
            "market-fair-nwr-negative-trap",
            "Market-fair but NWR-negative trap",
            "Trade Away Player",
            packages_for_mode("Trade Away Player"),
            ("Trap: market can look fair while NWR edge is poor.",),
            ("NWR negative",),
        ),
        TradeScenario(
            "nwr-positive-unrealistic-trap",
            "NWR-positive but unrealistic trap",
            "Trade For Player",
            packages_for_mode("Trade For Player"),
            ("Trap: NWR likes the deal but market realism may fail.",),
            ("unrealistic",),
        ),
        TradeScenario(
            "keeper-damage-trap",
            "Keeper-damage trap",
            "Trade For Player",
            packages_for_mode("Trade For Player"),
            ("Trap: do not include core keepers casually.",),
            ("keeper",),
        ),
        TradeScenario(
            "all-assets-untouchable-fallback",
            "All assets untouchable fallback",
            "Trade For Player",
            all_untouchable,
            (empty_state_message("Trade For Player"),),
            ("fallback",),
        ),
    )


def scenario_titles() -> tuple[str, ...]:
    return tuple(scenario.title for scenario in build_trade_scenarios())
