from __future__ import annotations

from dataclasses import dataclass

from src.trading_lab.trade_value_contracts import TradeReview


@dataclass(frozen=True)
class TradeExplanation:
    nwr_edge: str
    market_fairness: str
    opponent_fit: str
    roster_impact: str
    keeper_drop_impact: str
    risk_notes: tuple[str, ...]
    summary: str
    trust_labels: tuple[str, ...] = ()


def explain_nwr_edge(review: TradeReview) -> str:
    return f"NWR edge: fixture NWR delta is {review.score.nwr_delta:+.1f}."


def explain_market_fairness(review: TradeReview) -> str:
    return (
        "Market fairness: "
        f"fixture public fantasy delta is {review.score.public_market_delta:+.1f} "
        f"and labels as {review.score.market_fairness}."
    )


def explain_opponent_fit(review: TradeReview) -> str:
    needs = ", ".join(review.package.opponent_context.roster_needs) or "no fixture needs"
    return f"Opponent fit: {review.score.opponent_fit}; fixture needs are {needs}."


def explain_roster_impact(review: TradeReview) -> str:
    return f"Roster impact: {review.score.roster_impact}."


def explain_keeper_drop_impact(review: TradeReview) -> str:
    return f"Keeper/drop impact: {review.score.keeper_drop_impact}."


def explain_risk_flags(review: TradeReview) -> tuple[str, ...]:
    return (
        f"Risk label: {review.score.risk_label}.",
        "Manual review note: fixture values only; real integrations not wired.",
    )


def build_trade_explanation(review: TradeReview) -> TradeExplanation:
    return TradeExplanation(
        nwr_edge=explain_nwr_edge(review),
        market_fairness=explain_market_fairness(review),
        opponent_fit=explain_opponent_fit(review),
        roster_impact=explain_roster_impact(review),
        keeper_drop_impact=explain_keeper_drop_impact(review),
        risk_notes=explain_risk_flags(review),
        summary="Review note only; compare package details before any fantasy trade discussion.",
        trust_labels=build_trust_labels(review),
    )


def explain_why_nwr_likes_this(review: TradeReview) -> str:
    return f"Why NWR likes this: fixture NWR edge is {review.score.nwr_delta:+.1f}."


def explain_why_other_team_might_accept(review: TradeReview) -> str:
    return f"Why the other team might accept: {review.score.opponent_fit}."


def explain_why_market_fairness_may_mislead(review: TradeReview) -> str:
    return (
        "Why market fairness may be misleading: public fantasy value is separate "
        f"from NWR value and currently labels as {review.score.market_fairness}."
    )


def explain_what_could_go_wrong(review: TradeReview) -> str:
    return f"What could go wrong: {review.score.risk_label}; manual review required."


def build_trust_labels(review: TradeReview) -> tuple[str, ...]:
    return (
        "Fixture-only caveat",
        "Manual review required",
        "NWR value and public fantasy market value are separate",
        explain_why_nwr_likes_this(review),
        explain_why_other_team_might_accept(review),
        explain_why_market_fairness_may_mislead(review),
        explain_what_could_go_wrong(review),
    )
