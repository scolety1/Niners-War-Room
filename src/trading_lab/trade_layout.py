from __future__ import annotations

from src.trading_lab.trade_comparison import PackageComparisonRow
from src.trading_lab.trade_lab_ui import DemoTradePackage, empty_state_message


def format_asset_name(name: str, max_length: int = 40) -> str:
    if len(name) <= max_length:
        return name
    return f"{name[: max_length - 3]}..."


def format_warning_stack(warnings: tuple[str, ...], limit: int = 4) -> tuple[str, ...]:
    if len(warnings) <= limit:
        return warnings
    remaining = len(warnings) - limit
    return (*warnings[:limit], f"+{remaining} more warnings for manual review")


def no_package_layout_message(mode: str) -> str:
    return empty_state_message(mode)


def compact_negotiation_note(note: str, max_length: int = 80) -> str:
    return format_asset_name(note, max_length=max_length)


def compact_package_row(package: DemoTradePackage, rank: int) -> PackageComparisonRow:
    return PackageComparisonRow(
        rank=rank,
        give=" + ".join(format_asset_name(asset) for asset in package.give),
        get=" + ".join(format_asset_name(asset) for asset in package.get),
        nwr_gain=package.nwr_gain,
        public_market_fairness=package.public_market_fairness,
        opponent_fit=package.opponent_fit,
        roster_impact=package.roster_impact,
        keeper_drop_impact=package.keeper_drop_impact,
        risk=", ".join(package.risk_flags),
        verdict=package.verdict,
            primary_warning="; ".join(format_warning_stack(package.warnings, limit=1))
            if package.warnings
            else "No warning",
    )


def provider_status_panel_labels(status_labels: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(f"Provider status: {label}" for label in status_labels)
