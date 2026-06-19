from __future__ import annotations

from src.trading_lab.trade_value_contracts import PackageScore, TradePackage, TradeReview


def calculate_nwr_delta(package: TradePackage) -> float:
    return round(package.get_side.nwr_value_total - package.give_side.nwr_value_total, 2)


def calculate_public_market_delta(package: TradePackage) -> float:
    return round(
        package.get_side.public_market_value_total
        - package.give_side.public_market_value_total,
        2,
    )


def score_market_fairness(public_market_delta: float) -> str:
    if abs(public_market_delta) <= 5:
        return "market-fair"
    if public_market_delta > 5:
        return "unrealistic ask"
    return "favorable to opponent"


def score_opponent_fit(package: TradePackage) -> str:
    give_positions = {asset.position for asset in package.give_side.assets if asset.position}
    needs = " ".join(package.opponent_context.roster_needs).upper()
    if any(position and position in needs for position in give_positions):
        return "strong opponent fit"
    if package.opponent_context.roster_needs:
        return "medium opponent fit"
    return "low opponent fit"


def score_roster_impact(nwr_delta: float) -> str:
    if nwr_delta >= 15:
        return "major NWR roster gain"
    if nwr_delta > 0:
        return "positive NWR roster gain"
    if nwr_delta == 0:
        return "neutral roster impact"
    return "negative NWR roster impact"


def score_keeper_drop_impact(package: TradePackage) -> str:
    given_tags = {asset.drop_pressure_tag for asset in package.give_side.assets}
    received_keeper = {
        asset.keeper_status for asset in package.get_side.assets if asset.asset_type == "player"
    }
    if "high" in given_tags:
        return "drop pressure improves"
    if any("core" in status for status in received_keeper):
        return "keeper structure improves"
    return "manual keeper/drop review"


def score_risk(package: TradePackage, nwr_delta: float, public_market_delta: float) -> str:
    if nwr_delta < 0:
        return "walk-away review"
    if public_market_delta > 12:
        return "market realism risk"
    if any(asset.keeper_status == "core" for asset in package.give_side.assets):
        return "keeper cost risk"
    return "standard review"


def build_package_score(package: TradePackage) -> PackageScore:
    nwr_delta = calculate_nwr_delta(package)
    public_market_delta = calculate_public_market_delta(package)
    return PackageScore(
        nwr_delta=nwr_delta,
        public_market_delta=public_market_delta,
        market_fairness=score_market_fairness(public_market_delta),
        opponent_fit=score_opponent_fit(package),
        roster_impact=score_roster_impact(nwr_delta),
        keeper_drop_impact=score_keeper_drop_impact(package),
        risk_label=score_risk(package, nwr_delta, public_market_delta),
    )


def build_review_verdict(score: PackageScore) -> str:
    if score.nwr_delta < 0:
        return "hold: NWR value loss"
    if score.market_fairness == "unrealistic ask":
        return "hold: market realism concern"
    if score.nwr_delta >= 10 and "strong" in score.opponent_fit:
        return "review: strong fake package"
    return "review: compare alternatives"


def build_trade_review(package: TradePackage) -> TradeReview:
    score = build_package_score(package)
    return TradeReview(package=package, score=score, verdict=build_review_verdict(score))
