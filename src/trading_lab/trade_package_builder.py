from __future__ import annotations

from src.trading_lab.trade_lab_fixtures import asset_by_name, team_context_by_name
from src.trading_lab.trade_scoring import build_trade_review
from src.trading_lab.trade_value_contracts import TradePackage, TradeReview, TradeSide


def _package(
    package_id: str,
    mode: str,
    give: tuple[str, ...],
    get: tuple[str, ...],
    opponent_team: str,
) -> TradePackage:
    return TradePackage(
        package_id=package_id,
        mode=mode,
        give_side=TradeSide(
            team_name="NWR",
            assets=tuple(asset_by_name(name) for name in give),
            notes=("manual review side",),
        ),
        get_side=TradeSide(
            team_name=opponent_team,
            assets=tuple(asset_by_name(name) for name in get),
            notes=("fixture return side",),
        ),
        opponent_context=team_context_by_name(opponent_team),
        notes=("negotiation ladder placeholder", "fixture-only candidate"),
    )


def build_trade_for_candidates() -> tuple[TradePackage, ...]:
    return (
        _package(
            "trade-for-1",
            "Trade For Player",
            ("Player A", "2026 3rd"),
            ("Target Player",),
            "Team Alpha",
        ),
        _package(
            "trade-for-2",
            "Trade For Player",
            ("Player A", "2026 2nd"),
            ("Target Player",),
            "Team Alpha",
        ),
        _package(
            "trade-for-3",
            "Trade For Player",
            ("Player B",),
            ("Target Player", "2026 3rd"),
            "Team Alpha",
        ),
    )


def build_trade_away_candidates() -> tuple[TradePackage, ...]:
    return (
        _package(
            "trade-away-1",
            "Trade Away Player",
            ("Player B",),
            ("Player C", "2026 2nd"),
            "Team Bravo",
        ),
        _package(
            "trade-away-2",
            "Trade Away Player",
            ("Player A",),
            ("Player C", "2026 3rd"),
            "Team Bravo",
        ),
    )


def build_upgrade_position_candidates() -> tuple[TradePackage, ...]:
    return (
        _package(
            "upgrade-1",
            "Upgrade Position",
            ("Player C", "2026 2nd"),
            ("Target Player",),
            "Team Charlie",
        ),
        _package(
            "upgrade-2",
            "Upgrade Position",
            ("Player A", "Player D"),
            ("Player B",),
            "Team Charlie",
        ),
    )


def build_pick_conversion_candidates() -> tuple[TradePackage, ...]:
    return (
        _package(
            "pick-conversion-1",
            "Pick Conversion",
            ("2026 2nd",),
            ("Player D",),
            "Team Bravo",
        ),
        _package(
            "pick-conversion-2",
            "Pick Conversion",
            ("2026 3rd",),
            ("Player D",),
            "Team Bravo",
        ),
    )


def build_drop_pressure_candidates() -> tuple[TradePackage, ...]:
    return (
        _package(
            "drop-pressure-1",
            "Drop-Pressure Trade",
            ("Player D", "2026 3rd"),
            ("2026 2nd",),
            "Team Alpha",
        ),
        _package(
            "drop-pressure-2",
            "Drop-Pressure Trade",
            ("Player A",),
            ("2026 2nd", "2026 3rd"),
            "Team Alpha",
        ),
    )


def candidate_packages_for_mode(mode: str) -> tuple[TradePackage, ...]:
    builders = {
        "Trade For Player": build_trade_for_candidates,
        "Trade Away Player": build_trade_away_candidates,
        "Upgrade Position": build_upgrade_position_candidates,
        "Consolidate Depth": build_upgrade_position_candidates,
        "Pick Conversion": build_pick_conversion_candidates,
        "Drop-Pressure Trade": build_drop_pressure_candidates,
        "Opponent-Fit Trade": build_trade_for_candidates,
    }
    return builders.get(mode, build_trade_for_candidates)()


def rank_candidate_packages(packages: tuple[TradePackage, ...]) -> tuple[TradeReview, ...]:
    reviews = tuple(build_trade_review(package) for package in packages)
    return tuple(
        sorted(
            reviews,
            key=lambda review: (
                review.score.nwr_delta,
                review.score.market_fairness == "market-fair",
                "strong" in review.score.opponent_fit,
            ),
            reverse=True,
        )
    )
