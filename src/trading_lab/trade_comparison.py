from __future__ import annotations

from dataclasses import dataclass

from src.trading_lab.trade_lab_ui import DemoTradePackage, packages_for_mode

COMPARISON_COLUMNS = (
    "rank",
    "give",
    "get",
    "NWR gain",
    "public market fairness",
    "opponent fit",
    "roster impact",
    "keeper/drop impact",
    "risk",
    "verdict",
    "primary warning",
)


@dataclass(frozen=True)
class PackageComparisonRow:
    rank: int
    give: str
    get: str
    nwr_gain: float
    public_market_fairness: str
    opponent_fit: str
    roster_impact: str
    keeper_drop_impact: str
    risk: str
    verdict: str
    primary_warning: str


def build_package_comparison_rows(
    packages: tuple[DemoTradePackage, ...],
) -> tuple[PackageComparisonRow, ...]:
    sorted_packages = tuple(
        sorted(
            packages,
            key=lambda package: (package.nwr_gain, package.public_market_fairness),
            reverse=True,
        )
    )
    return tuple(
        PackageComparisonRow(
            rank=index,
            give=" + ".join(package.give),
            get=" + ".join(package.get),
            nwr_gain=package.nwr_gain,
            public_market_fairness=package.public_market_fairness,
            opponent_fit=package.opponent_fit,
            roster_impact=package.roster_impact,
            keeper_drop_impact=package.keeper_drop_impact,
            risk=", ".join(package.risk_flags),
            verdict=package.verdict,
            primary_warning=package.warnings[0] if package.warnings else "No warning",
        )
        for index, package in enumerate(sorted_packages, start=1)
    )


def comparison_rows_for_mode(mode: str) -> tuple[PackageComparisonRow, ...]:
    return build_package_comparison_rows(packages_for_mode(mode))
