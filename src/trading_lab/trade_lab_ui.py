from __future__ import annotations

from dataclasses import dataclass

TRADE_LAB_TITLE = "Trade Lab"
TRADE_LAB_SUBTITLE = (
    "Find realistic fantasy trades where market says fair, but NWR says we win."
)

TRADE_LAB_MODES = (
    "Trade For Player",
    "Trade Away Player",
    "Upgrade Position",
    "Consolidate Depth",
    "Pick Conversion",
    "Drop-Pressure Trade",
    "Opponent-Fit Trade",
    "Training Mode",
)

TRADE_LAB_DATA_CHIPS = (
    "NWR private value placeholder",
    "Public fantasy market value placeholder",
    "Roster context placeholder",
    "Drop pressure placeholder",
    "Rookie/draft context placeholder",
    "Manual review required",
)

PROHIBITED_DEMO_TERMS = (
    "stock",
    "broker",
    "api",
    "equity",
    "crypto",
    "order execution",
)


@dataclass(frozen=True)
class NegotiationLadder:
    opening_offer: str
    fair_offer: str
    max_offer: str
    walk_away: str


@dataclass(frozen=True)
class RosterAftermath:
    summary: str
    keeper_impact: str
    drop_pressure_impact: str
    positional_depth_impact: str
    rookie_mock_context: str


@dataclass(frozen=True)
class DemoTradePackage:
    mode: str
    give: tuple[str, ...]
    get: tuple[str, ...]
    nwr_gain: float
    public_market_fairness: str
    opponent_fit: str
    roster_impact: str
    keeper_drop_impact: str
    risk_flags: tuple[str, ...]
    verdict: str
    negotiation_ladder: NegotiationLadder
    warnings: tuple[str, ...]
    roster_aftermath: RosterAftermath


def demo_trade_packages() -> tuple[DemoTradePackage, ...]:
    return (
        DemoTradePackage(
            mode="Trade For Player",
            give=("Player A", "2026 3rd"),
            get=("Target Player",),
            nwr_gain=18.4,
            public_market_fairness="Fair enough for Team Alpha to consider.",
            opponent_fit="Team Alpha needs depth and can spare Target Player.",
            roster_impact="Upgrades starting lineup while trimming bench crowding.",
            keeper_drop_impact="Improves keeper ceiling and lowers drop pressure.",
            risk_flags=("Target role uncertainty", "Pick cost acceptable"),
            verdict="Best opening package for manual review",
            negotiation_ladder=NegotiationLadder(
                opening_offer="Player A",
                fair_offer="Player A plus 2026 3rd",
                max_offer="Player A plus 2026 2nd",
                walk_away="Player A plus Player B",
            ),
            warnings=("Do not include Player B unless Team Alpha adds value.",),
            roster_aftermath=RosterAftermath(
                summary="Starting lineup gains a higher-upside player.",
                keeper_impact="Keeper pool improves by one high-ceiling option.",
                drop_pressure_impact="Bench consolidation eases one future cut.",
                positional_depth_impact="Depth remains acceptable after the trade.",
                rookie_mock_context="2026 3rd is below current priority pick tier.",
            ),
        ),
        DemoTradePackage(
            mode="Trade Away Player",
            give=("Player B",),
            get=("Player C", "2026 2nd"),
            nwr_gain=11.2,
            public_market_fairness="Slightly favorable but realistic for Team Bravo.",
            opponent_fit="Team Bravo needs Player B's position and has extra picks.",
            roster_impact="Adds flexibility and a rookie pick without hurting starters.",
            keeper_drop_impact="Keeper impact neutral; drop pressure improves.",
            risk_flags=("Player C role volatility",),
            verdict="Strong counteroffer package",
            negotiation_ladder=NegotiationLadder(
                opening_offer="Player C plus 2026 3rd",
                fair_offer="Player C plus 2026 2nd",
                max_offer="Player C plus 2026 2nd and bench sweetener",
                walk_away="Player C only",
            ),
            warnings=("Avoid accepting Player C without a pick.",),
            roster_aftermath=RosterAftermath(
                summary="Roster becomes more flexible across bye weeks.",
                keeper_impact="No new keeper crowding.",
                drop_pressure_impact="Creates one cleaner drop path.",
                positional_depth_impact="Slight short-term depth loss at Player B's spot.",
                rookie_mock_context="2026 2nd supports next rookie draft plan.",
            ),
        ),
    )


def best_trade_package(packages: tuple[DemoTradePackage, ...] | None = None) -> DemoTradePackage:
    candidates = packages or demo_trade_packages()
    return max(candidates, key=lambda package: package.nwr_gain)


def format_package_summary(package: DemoTradePackage) -> str:
    give = " + ".join(package.give)
    get = " + ".join(package.get)
    return f"Give {give} for {get}: +{package.nwr_gain:.1f} NWR value"


def bad_trade_warnings(package: DemoTradePackage) -> tuple[str, ...]:
    warnings = list(package.warnings)
    if package.nwr_gain < 0:
        warnings.append("NWR value delta is negative.")
    if "unrealistic" in package.public_market_fairness.lower():
        warnings.append("Public fantasy market value says this may not be realistic.")
    return tuple(warnings)


def demo_payload_text() -> str:
    packages = demo_trade_packages()
    return " ".join(
        [
            TRADE_LAB_TITLE,
            TRADE_LAB_SUBTITLE,
            " ".join(TRADE_LAB_MODES),
            " ".join(TRADE_LAB_DATA_CHIPS),
            " ".join(format_package_summary(package) for package in packages),
            " ".join(package.verdict for package in packages),
        ]
    )
