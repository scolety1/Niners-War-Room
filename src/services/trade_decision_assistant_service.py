"""Transparent advisory trade decisions built from governed owner evidence.

The assistant deliberately avoids a cross-authority package value.  Each named dimension is
evaluated ordinally, and the final recommendation follows documented agreement,
contradiction, and evidence-coverage rules.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

from src.services.draft_day_trade_lab_service import TradeState, trade_item_rows

AUTHORITY = "ADVISORY_DECISION_SUPPORT"
TEAM_WINDOWS = ("Contending", "Balanced", "Rebuilding")
RECOMMENDATIONS = (
    "ACCEPT",
    "LEAN_ACCEPT",
    "COUNTER",
    "LEAN_REJECT",
    "REJECT",
    "TOO_CLOSE",
    "INSUFFICIENT_EVIDENCE",
)
DIMENSION_OUTCOMES = (
    "SIDE_A_CLEAR",
    "SIDE_A_LEAN",
    "EVEN",
    "SIDE_B_LEAN",
    "SIDE_B_CLEAR",
    "UNKNOWN",
)
CONFIDENCE_LEVELS = ("HIGH", "MEDIUM", "LOW")

DimensionOutcome = Literal[
    "SIDE_A_CLEAR",
    "SIDE_A_LEAN",
    "EVEN",
    "SIDE_B_LEAN",
    "SIDE_B_CLEAR",
    "UNKNOWN",
]
Confidence = Literal["HIGH", "MEDIUM", "LOW"]
Recommendation = Literal[
    "ACCEPT",
    "LEAN_ACCEPT",
    "COUNTER",
    "LEAN_REJECT",
    "REJECT",
    "TOO_CLOSE",
    "INSUFFICIENT_EVIDENCE",
]


@dataclass(frozen=True)
class DecisionDimension:
    code: str
    label: str
    outcome: DimensionOutcome
    confidence: Confidence
    evidence: tuple[str, ...]
    explanation: str


@dataclass(frozen=True)
class CounterSuggestion:
    counter_id: str
    title: str
    give: tuple[str, ...]
    receive: tuple[str, ...]
    changes: tuple[str, ...]
    why: str
    ownership_note: str = "Uses only current-trade assets."


@dataclass(frozen=True)
class TradeDecision:
    authority: str
    recommendation: Recommendation
    preferred_side: str
    confidence: Confidence
    team_window: str
    summary: str
    reasons: tuple[str, ...]
    main_uncertainty: str
    what_would_change: tuple[str, ...]
    dimensions: tuple[DecisionDimension, ...]
    synthesis_trace: tuple[str, ...]
    counters: tuple[CounterSuggestion, ...]


@dataclass(frozen=True)
class CounterComparison:
    changes: tuple[str, ...]
    recommendation_before: str
    recommendation_after: str
    improved_dimensions: tuple[str, ...]


def evaluate_trade_decision(
    state: TradeState,
    lookup: Mapping[str, Mapping[str, object]],
    *,
    team_window: str = "Balanced",
) -> TradeDecision:
    """Evaluate a trade without producing a package score or cross-authority conversion."""

    if team_window not in TEAM_WINDOWS:
        raise ValueError(f"Unsupported team window: {team_window}")
    rows = trade_item_rows(state, dict(lookup))
    give = rows.loc[rows["side"].eq("You give")].to_dict("records")
    receive = rows.loc[rows["side"].eq("You receive")].to_dict("records")
    if not give or not receive:
        return _insufficient(team_window, "Both trade sides need at least one governed asset.")

    dimensions = (
        _best_asset(give, receive),
        _established_standing(give, receive),
        _youth_window(give, receive),
        _production_certainty(give, receive),
        _upside_uncertainty(give, receive),
        _future_flexibility(give, receive),
        _league_fit(give, receive),
        _team_window_fit(give, receive, team_window),
        _outcome_risk(give, receive),
        _market_corroboration(give, receive),
    )
    if _evidence_is_insufficient(give, receive, dimensions):
        uncertainty = _main_uncertainty(give, receive, dimensions)
        return TradeDecision(
            authority=AUTHORITY,
            recommendation="INSUFFICIENT_EVIDENCE",
            preferred_side="No side",
            confidence="LOW",
            team_window=team_window,
            summary="The admitted evidence is too incomplete to support a side preference.",
            reasons=(
                "Too many decision dimensions are unknown or depend on blocked evidence.",
                "Missing evidence is not treated as zero and no substitute package value "
                "is created.",
            ),
            main_uncertainty=uncertainty,
            what_would_change=(
                "Obtain governed evidence for the blocked or unsupported assets.",
                "Replace an unsupported asset with a governed player or pick class.",
            ),
            dimensions=dimensions,
            synthesis_trace=_synthesis_trace(dimensions),
            counters=(),
        )

    recommendation, preferred = _synthesize(dimensions)
    confidence = _decision_confidence(dimensions, give, receive)
    reasons = _strongest_reasons(dimensions, preferred)
    uncertainty = _main_uncertainty(give, receive, dimensions)
    changes = _what_would_change(give, receive, preferred)
    return TradeDecision(
        authority=AUTHORITY,
        recommendation=recommendation,
        preferred_side=preferred,
        confidence=confidence,
        team_window=team_window,
        summary=_decision_summary(recommendation, preferred, team_window),
        reasons=reasons,
        main_uncertainty=uncertainty,
        what_would_change=changes,
        dimensions=dimensions,
        synthesis_trace=_synthesis_trace(dimensions),
        # Specific counters require separately proven owner/opponent ownership.  The
        # roster-aware negotiation adapter supplies them; this evidence-only engine
        # never falls back to generic or inferred targets.
        counters=(),
    )


def evaluate_team_windows(
    state: TradeState,
    lookup: Mapping[str, Mapping[str, object]],
) -> tuple[TradeDecision, ...]:
    return tuple(
        evaluate_trade_decision(state, lookup, team_window=value) for value in TEAM_WINDOWS
    )


def compare_counter_decisions(
    original: TradeDecision,
    current: TradeDecision,
    counter: CounterSuggestion,
) -> CounterComparison:
    before = {row.code: row for row in original.dimensions}
    improved = tuple(
        row.label
        for row in current.dimensions
        if row.code in before
        and _direction_value(row.outcome) > _direction_value(before[row.code].outcome)
    )
    return CounterComparison(
        changes=counter.changes,
        recommendation_before=f"{original.recommendation} · {original.confidence}",
        recommendation_after=f"{current.recommendation} · {current.confidence}",
        improved_dimensions=improved,
    )


def _dimension(
    code: str,
    label: str,
    outcome: DimensionOutcome,
    confidence: Confidence,
    evidence: Sequence[str],
    explanation: str,
) -> DecisionDimension:
    return DecisionDimension(code, label, outcome, confidence, tuple(evidence), explanation)


def _best_asset(
    give: list[dict[str, object]], receive: list[dict[str, object]]
) -> DecisionDimension:
    a = _best_ranked(give)
    b = _best_ranked(receive)
    if not a and not b:
        return _dimension(
            "D1",
            "Best asset",
            "UNKNOWN",
            "LOW",
            ("Neither side has a Finished V1 production-ranked player.",),
            "Rookie and pick authorities are not converted onto the Finished V1 scale.",
        )
    if not a or not b:
        winner, side = (a, "SIDE_A") if a else (b, "SIDE_B")
        other = receive if a else give
        strength = "LEAN" if any(_is_rookie(row) or _is_pick(row) for row in other) else "CLEAR"
        outcome = f"{side}_{strength}"
        assert winner is not None and outcome in DIMENSION_OUTCOMES
        evidence = (f"{winner[0]} is the only production-ranked anchor (Rank {winner[1]}).",)
        return _dimension(
            "D1",
            "Best asset",
            outcome,  # type: ignore[arg-type]
            "MEDIUM",
            evidence,
            "Unscaled rookie or pick evidence prevents stronger cross-authority certainty.",
        )
    a_band = _rank_band(a[1])
    b_band = _rank_band(b[1])
    evidence = (
        f"You give: {a[0]} (Rank {a[1]}, {a_band[1]}).",
        f"You receive: {b[0]} (Rank {b[1]}, {b_band[1]}).",
    )
    difference = abs(a_band[0] - b_band[0])
    if a_band[0] == b_band[0]:
        outcome: DimensionOutcome = "EVEN"
        explanation = "Both best assets occupy the same declared production-rank band."
    else:
        side = "SIDE_A" if a_band[0] < b_band[0] else "SIDE_B"
        strength = "CLEAR" if difference >= 2 else "LEAN"
        outcome = f"{side}_{strength}"  # type: ignore[assignment]
        explanation = "The preference follows rank-band separation, not a rank-point total."
    return _dimension("D1", "Best asset", outcome, "HIGH", evidence, explanation)


def _established_standing(
    give: list[dict[str, object]], receive: list[dict[str, object]]
) -> DecisionDimension:
    a = sorted(_ranked_rows(give), key=lambda item: item[1])
    b = sorted(_ranked_rows(receive), key=lambda item: item[1])
    if not a and not b:
        return _dimension(
            "D2",
            "Established dynasty standing",
            "UNKNOWN",
            "LOW",
            ("No Finished V1 production ranks are available.",),
            "No rookie-to-veteran rank conversion is allowed.",
        )
    evidence = (
        f"You give has {len(a)} production-ranked asset{'s' if len(a) != 1 else ''}.",
        f"You receive has {len(b)} production-ranked asset{'s' if len(b) != 1 else ''}.",
    )
    if len(a) != len(b):
        more_side = "SIDE_A" if len(a) > len(b) else "SIDE_B"
        more, fewer = (a, b) if len(a) > len(b) else (b, a)
        best_more = _rank_band(more[0][1])[0]
        best_fewer = _rank_band(fewer[0][1])[0] if fewer else 99
        if len(more) - len(fewer) >= 2 and best_more <= best_fewer:
            strength = "CLEAR"
            explanation = (
                "One side has materially more established depth without giving up the "
                "better rank band."
            )
        else:
            strength = "LEAN"
            explanation = (
                "Established depth favors one side, but the opposing premium asset keeps "
                "the result mixed."
            )
        outcome = f"{more_side}_{strength}"
        return _dimension(
            "D2",
            "Established dynasty standing",
            outcome,  # type: ignore[arg-type]
            "HIGH",
            evidence,
            explanation,
        )
    if not a:
        outcome = "EVEN"
    else:
        a_bands = [_rank_band(rank)[0] for _, rank in a]
        b_bands = [_rank_band(rank)[0] for _, rank in b]
        a_no_worse = all(left <= right for left, right in zip(a_bands, b_bands, strict=True))
        b_no_worse = all(right <= left for left, right in zip(a_bands, b_bands, strict=True))
        if a_no_worse and a_bands != b_bands:
            outcome = "SIDE_A_LEAN"
        elif b_no_worse and a_bands != b_bands:
            outcome = "SIDE_B_LEAN"
        else:
            outcome = "EVEN"
    return _dimension(
        "D2",
        "Established dynasty standing",
        outcome,
        "HIGH",
        evidence,
        "Sorted rank-band dominance is used; ranks are not averaged or summed.",
    )


def _youth_window(
    give: list[dict[str, object]], receive: list[dict[str, object]]
) -> DecisionDimension:
    a_young, a_risk = _youth_and_age_risk(give)
    b_young, b_risk = _youth_and_age_risk(receive)
    evidence = (
        f"You give: {a_young} young/rookie asset(s), {a_risk} age-window caution(s).",
        f"You receive: {b_young} young/rookie asset(s), {b_risk} age-window caution(s).",
    )
    if not any((a_young, a_risk, b_young, b_risk)):
        outcome: DimensionOutcome = "UNKNOWN"
        confidence: Confidence = "LOW"
    else:
        a_better = a_young > b_young or a_risk < b_risk
        b_better = b_young > a_young or b_risk < a_risk
        if a_better and not b_better:
            outcome = (
                "SIDE_A_CLEAR" if (a_young - b_young) + (b_risk - a_risk) >= 2 else "SIDE_A_LEAN"
            )
        elif b_better and not a_better:
            outcome = (
                "SIDE_B_CLEAR" if (b_young - a_young) + (a_risk - b_risk) >= 2 else "SIDE_B_LEAN"
            )
        else:
            outcome = "EVEN"
        confidence = "MEDIUM"
    return _dimension(
        "D3",
        "Youth / career window",
        outcome,
        confidence,
        evidence,
        "Rookie status, known age, and explicit lifecycle caveats determine this ordinal result.",
    )


def _production_certainty(
    give: list[dict[str, object]], receive: list[dict[str, object]]
) -> DecisionDimension:
    a = len(_ranked_rows(give))
    b = len(_ranked_rows(receive))
    evidence = (
        f"You give: {a} Finished V1 production-ranked asset(s).",
        f"You receive: {b} Finished V1 production-ranked asset(s).",
    )
    if a == b:
        outcome: DimensionOutcome = "EVEN" if a else "UNKNOWN"
    else:
        side = "SIDE_A" if a > b else "SIDE_B"
        strength = "CLEAR" if abs(a - b) >= 2 else "LEAN"
        outcome = f"{side}_{strength}"  # type: ignore[assignment]
    return _dimension(
        "D4",
        "Production certainty",
        outcome,
        "HIGH" if a or b else "LOW",
        evidence,
        "Finished V1 coverage is counted; rookie review evidence remains separate.",
    )


def _upside_uncertainty(
    give: list[dict[str, object]], receive: list[dict[str, object]]
) -> DecisionDimension:
    a = sum(_is_rookie(row) for row in give) + sum(
        _known_age(row) <= 25 for row in give if _known_age(row)
    )
    b = sum(_is_rookie(row) for row in receive) + sum(
        _known_age(row) <= 25 for row in receive if _known_age(row)
    )
    evidence = (
        f"You give has {a} supported youth/upside signal(s).",
        f"You receive has {b} supported youth/upside signal(s).",
    )
    if a == b:
        outcome: DimensionOutcome = "EVEN" if a else "UNKNOWN"
    else:
        side = "SIDE_A" if a > b else "SIDE_B"
        strength = "CLEAR" if abs(a - b) >= 2 else "LEAN"
        outcome = f"{side}_{strength}"  # type: ignore[assignment]
    return _dimension(
        "D5",
        "Upside / uncertainty",
        outcome,
        "MEDIUM" if a or b else "LOW",
        evidence,
        "This identifies upside exposure and its uncertainty; it does not convert upside "
        "to production value.",
    )


def _future_flexibility(
    give: list[dict[str, object]], receive: list[dict[str, object]]
) -> DecisionDimension:
    a = sorted((_pick_profile(row) for row in give if _is_pick(row)), key=lambda item: item[:2])
    b = sorted((_pick_profile(row) for row in receive if _is_pick(row)), key=lambda item: item[:2])
    evidence = (
        "You give picks: " + (", ".join(item[2] for item in a) or "none"),
        "You receive picks: " + (", ".join(item[2] for item in b) or "none"),
    )
    if not a and not b:
        outcome: DimensionOutcome = "EVEN"
    elif not a or not b:
        outcome = "SIDE_A_LEAN" if a else "SIDE_B_LEAN"
    elif a[0][0] != b[0][0]:
        outcome = "SIDE_A_CLEAR" if a[0][0] < b[0][0] else "SIDE_B_CLEAR"
    elif a[0][1] != b[0][1]:
        outcome = "SIDE_A_LEAN" if a[0][1] < b[0][1] else "SIDE_B_LEAN"
    else:
        outcome = "EVEN"
    return _dimension(
        "D6",
        "Future flexibility",
        outcome,
        "MEDIUM" if a or b else "HIGH",
        evidence,
        "Round precedes year; unknown slots lower confidence. No player-equivalent pick "
        "value is created.",
    )


def _league_fit(
    give: list[dict[str, object]], receive: list[dict[str, object]]
) -> DecisionDimension:
    a_limited = sum(_limited_one_qb(row) for row in give)
    b_limited = sum(_limited_one_qb(row) for row in receive)
    a_flex = sum(str(row.get("position")) in {"RB", "WR", "TE"} for row in give)
    b_flex = sum(str(row.get("position")) in {"RB", "WR", "TE"} for row in receive)
    evidence = (
        f"You give: {a_limited} replacement-limited QB(s), {a_flex} RB/WR/TE asset(s).",
        f"You receive: {b_limited} replacement-limited QB(s), {b_flex} RB/WR/TE asset(s).",
    )
    if a_limited != b_limited:
        outcome: DimensionOutcome = "SIDE_A_LEAN" if a_limited < b_limited else "SIDE_B_LEAN"
    elif a_flex != b_flex:
        outcome = "SIDE_A_LEAN" if a_flex > b_flex else "SIDE_B_LEAN"
    else:
        outcome = "EVEN"
    return _dimension(
        "D7",
        "Position / league fit",
        outcome,
        "HIGH",
        evidence,
        "The declared 10-team, 1QB, 3WR, 2FLEX format limits replacement-level QB "
        "scarcity and rewards RB/WR/TE utility.",
    )


def _team_window_fit(
    give: list[dict[str, object]], receive: list[dict[str, object]], team_window: str
) -> DecisionDimension:
    a_ranked, b_ranked = len(_ranked_rows(give)), len(_ranked_rows(receive))
    a_young, a_risk = _youth_and_age_risk(give)
    b_young, b_risk = _youth_and_age_risk(receive)
    a_pick = min((_pick_profile(row)[0] for row in give if _is_pick(row)), default=99)
    b_pick = min((_pick_profile(row)[0] for row in receive if _is_pick(row)), default=99)
    evidence = (
        f"Context: {team_window}.",
        f"Established assets: You give {a_ranked}; You receive {b_ranked}.",
        f"Youth/age-risk: You give {a_young}/{a_risk}; You receive {b_young}/{b_risk}.",
    )
    if team_window == "Contending":
        if a_ranked == b_ranked:
            outcome: DimensionOutcome = "EVEN"
        else:
            side = "SIDE_A" if a_ranked > b_ranked else "SIDE_B"
            risk_penalty = a_risk if side == "SIDE_A" else b_risk
            strength = "CLEAR" if abs(a_ranked - b_ranked) >= 2 and risk_penalty == 0 else "LEAN"
            outcome = f"{side}_{strength}"  # type: ignore[assignment]
        explanation = (
            "Contending prioritizes established production, moderated by active lifecycle cautions."
        )
    elif team_window == "Rebuilding":
        a_better = a_young > b_young or a_risk < b_risk or a_pick < b_pick
        b_better = b_young > a_young or b_risk < a_risk or b_pick < a_pick
        if a_better and not b_better:
            outcome = "SIDE_A_CLEAR"
        elif b_better and not a_better:
            outcome = "SIDE_B_CLEAR"
        elif a_better and b_better:
            outcome = "SIDE_A_LEAN" if (a_pick, -a_young) < (b_pick, -b_young) else "SIDE_B_LEAN"
        else:
            outcome = "EVEN"
        explanation = (
            "Rebuilding prioritizes youth, lifecycle runway, and earlier-round future flexibility."
        )
    else:
        a_best = _best_ranked(give)
        b_best = _best_ranked(receive)
        signals: list[str] = []
        if a_best and b_best and _rank_band(a_best[1])[0] != _rank_band(b_best[1])[0]:
            signals.append("A" if _rank_band(a_best[1])[0] < _rank_band(b_best[1])[0] else "B")
        if a_pick != b_pick:
            signals.append("A" if a_pick < b_pick else "B")
        if (a_young - a_risk) != (b_young - b_risk):
            signals.append("A" if (a_young - a_risk) > (b_young - b_risk) else "B")
        if signals and len(set(signals)) == 1:
            side = "SIDE_A" if signals[0] == "A" else "SIDE_B"
            outcome = f"{side}_{'CLEAR' if len(signals) >= 3 else 'LEAN'}"  # type: ignore[assignment]
        else:
            outcome = "EVEN"
        explanation = (
            "Balanced uses best-asset band, youth/runway, and pick class without changing "
            "source ranks."
        )
    return _dimension("D8", "Team-window fit", outcome, "MEDIUM", evidence, explanation)


def _outcome_risk(
    give: list[dict[str, object]], receive: list[dict[str, object]]
) -> DecisionDimension:
    a_risk = _risk_count(give)
    b_risk = _risk_count(receive)
    a_outcome = sum(bool(tuple(row.get("outcome_signals", ()))) for row in give)
    b_outcome = sum(bool(tuple(row.get("outcome_signals", ()))) for row in receive)
    evidence = (
        f"You give: {a_risk} major risk/uncertainty flag(s), {a_outcome} applicable "
        "Outcome context asset(s).",
        f"You receive: {b_risk} major risk/uncertainty flag(s), {b_outcome} applicable "
        "Outcome context asset(s).",
    )
    if a_risk == b_risk:
        outcome: DimensionOutcome = "EVEN" if (a_risk or a_outcome or b_outcome) else "UNKNOWN"
    else:
        side = "SIDE_A" if a_risk < b_risk else "SIDE_B"
        strength = "CLEAR" if abs(a_risk - b_risk) >= 2 else "LEAN"
        outcome = f"{side}_{strength}"  # type: ignore[assignment]
    return _dimension(
        "D9",
        "Outcome / risk context",
        outcome,
        "MEDIUM" if outcome != "UNKNOWN" else "LOW",
        evidence,
        "Lower supported lifecycle/blocked-evidence risk is preferred; Outcome signals "
        "are contextual, not summed.",
    )


def _market_corroboration(
    give: list[dict[str, object]], receive: list[dict[str, object]]
) -> DecisionDimension:
    a = _best_market(give)
    b = _best_market(receive)
    if not a or not b:
        return _dimension(
            "D10",
            "Market corroboration",
            "UNKNOWN",
            "LOW",
            ("Comparable individual market-rank evidence is unavailable on both sides.",),
            "Market evidence cannot fill missing primary evidence.",
        )
    a_band, b_band = _market_band(a[1]), _market_band(b[1])
    evidence = (
        f"You give best individual market rank: {a[0]} ({a[1]:g}; {a[2]}).",
        f"You receive best individual market rank: {b[0]} ({b[1]:g}; {b[2]}).",
        "No market side total is calculated.",
    )
    if a_band == b_band:
        outcome: DimensionOutcome = "EVEN"
    else:
        outcome = "SIDE_A_LEAN" if a_band < b_band else "SIDE_B_LEAN"
    return _dimension(
        "D10",
        "Market corroboration",
        outcome,
        "LOW",
        evidence,
        "Stale individual market evidence is secondary corroboration only.",
    )


def _synthesize(dimensions: Sequence[DecisionDimension]) -> tuple[Recommendation, str]:
    a = [row for row in dimensions if row.outcome in {"SIDE_A_CLEAR", "SIDE_A_LEAN"}]
    b = [row for row in dimensions if row.outcome in {"SIDE_B_CLEAR", "SIDE_B_LEAN"}]
    a_clear = sum(row.outcome == "SIDE_A_CLEAR" for row in dimensions)
    b_clear = sum(row.outcome == "SIDE_B_CLEAR" for row in dimensions)
    if len(a) == len(b):
        return (
            ("COUNTER", "Your current side")
            if (a_clear or b_clear)
            else ("TOO_CLOSE", "No clear side")
        )
    preferred_a = len(a) > len(b)
    preferred = "Your current side" if preferred_a else "The incoming side"
    support, oppose = (a, b) if preferred_a else (b, a)
    clear, opposing_clear = (a_clear, b_clear) if preferred_a else (b_clear, a_clear)
    margin = len(support) - len(oppose)
    if clear >= 2 and opposing_clear == 0 and margin >= 3:
        return ("REJECT" if preferred_a else "ACCEPT"), preferred
    if opposing_clear or (support and len(oppose) >= 2):
        return "COUNTER", preferred
    return ("LEAN_REJECT" if preferred_a else "LEAN_ACCEPT"), preferred


def _decision_confidence(
    dimensions: Sequence[DecisionDimension],
    give: Sequence[Mapping[str, object]],
    receive: Sequence[Mapping[str, object]],
) -> Confidence:
    known = [row for row in dimensions if row.outcome != "UNKNOWN"]
    a = sum(row.outcome.startswith("SIDE_A") for row in known)
    b = sum(row.outcome.startswith("SIDE_B") for row in known)
    cross_authority = any(_is_rookie(row) or _is_pick(row) for row in (*give, *receive))
    stale_market = any(
        "stale" in str(row.get("market_status", "")).casefold() for row in (*give, *receive)
    )
    if len(known) >= 9 and min(a, b) == 0 and not cross_authority and not stale_market:
        return "HIGH"
    if len(known) >= 7 and abs(a - b) >= 2:
        return "MEDIUM"
    return "LOW"


def _strongest_reasons(dimensions: Sequence[DecisionDimension], preferred: str) -> tuple[str, ...]:
    prefix = "SIDE_A" if preferred == "Your current side" else "SIDE_B"
    preferred_rows = [row for row in dimensions if row.outcome.startswith(prefix)]
    preferred_rows.sort(
        key=lambda row: (
            0 if row.outcome.endswith("CLEAR") else 1,
            0 if row.confidence == "HIGH" else 1 if row.confidence == "MEDIUM" else 2,
            row.code,
        )
    )
    reasons = [
        f"{row.label}: {row.explanation} {' '.join(row.evidence[:2])}" for row in preferred_rows[:5]
    ]
    return tuple(reasons) or ("No independent dimension establishes a reliable side preference.",)


def _main_uncertainty(
    give: Sequence[Mapping[str, object]],
    receive: Sequence[Mapping[str, object]],
    dimensions: Sequence[DecisionDimension],
) -> str:
    blocked = [str(row.get("player")) for row in (*give, *receive) if _is_blocked(row)]
    if blocked:
        return f"{', '.join(blocked)} has blocked evidence and cannot support a recommendation."
    rookies = [str(row.get("player")) for row in (*give, *receive) if _is_rookie(row)]
    if rookies:
        return (
            f"{', '.join(rookies)} cannot be placed on the Finished V1 production scale; "
            "rookie/research uncertainty is the largest unknown."
        )
    unknown_picks = [str(row.get("player")) for row in (*give, *receive) if _is_pick(row)]
    if unknown_picks:
        return (
            f"The exact slots for {', '.join(unknown_picks)} are unknown; only round/year "
            "context is admitted."
        )
    contradictory = [row.label for row in dimensions if row.outcome.endswith(("CLEAR", "LEAN"))]
    if contradictory:
        return (
            "Independent dimensions disagree, so roster context can legitimately change the lean."
        )
    return "The evidence is close and does not create a decisive structural edge."


def _what_would_change(
    give: Sequence[Mapping[str, object]],
    receive: Sequence[Mapping[str, object]],
    preferred: str,
) -> tuple[str, ...]:
    changes: list[str] = []
    if preferred == "Your current side":
        firsts = [str(row.get("player")) for row in give if _is_first_round_pick(row)]
        if firsts:
            changes.append(f"Keep {firsts[0]} on your side of the trade.")
        best = _best_ranked(list(give))
        if best:
            changes.append(f"Keep the premium outgoing anchor, {best[0]} (Rank {best[1]}).")
        if any(_age_risk(row) for row in receive):
            changes.append(
                "Replace an aging incoming veteran with a younger top-100 RB/WR/TE target profile."
            )
        if any(_limited_one_qb(row) for row in receive):
            changes.append(
                "Replace the replacement-limited incoming QB with meaningful non-QB depth "
                "or stronger future capital."
            )
    else:
        if any(_is_pick(row) for row in receive):
            changes.append(
                "Downgrading or removing the strongest incoming pick would weaken the accept case."
            )
        best = _best_ranked(list(receive))
        if best:
            changes.append(
                f"Removing {best[0]} would remove the incoming side's strongest production anchor."
            )
        changes.append(
            "A new lifecycle or role-risk flag on the incoming side would lower confidence."
        )
    return tuple(dict.fromkeys(changes))[:4]


def _suggest_counters(
    state: TradeState,
    lookup: Mapping[str, Mapping[str, object]],
    give_rows: Sequence[Mapping[str, object]],
    receive_rows: Sequence[Mapping[str, object]],
    preferred: str,
    team_window: str,
) -> tuple[CounterSuggestion, ...]:
    if preferred != "Your current side":
        return ()
    give = tuple(state.get("give", ()))
    receive = tuple(state.get("get", ()))
    suggestions: list[CounterSuggestion] = []
    first_key = next((key for key in give if _is_first_round_pick(lookup.get(key, {}))), "")
    if first_key and len(give) > 1:
        name = str(lookup[first_key].get("player"))
        suggestions.append(
            CounterSuggestion(
                "minimal-improvement",
                "Minimal improvement — keep the first-round pick",
                tuple(key for key in give if key != first_key),
                receive,
                (f"Remove {name} from You give.",),
                "This preserves the stronger future-capital class without inventing a "
                "pick-to-player value.",
            )
        )
    best = _best_ranked_key(give, lookup)
    if best and len(give) > 1:
        name = str(lookup[best].get("player"))
        suggestions.append(
            CounterSuggestion(
                "protect-best-asset",
                "Protect the best asset",
                tuple(key for key in give if key != best),
                receive,
                (f"Keep {name} out of the offer.",),
                "The counter protects the strongest Finished V1 production-ranked asset.",
            )
        )
    weak_pick = next(
        (
            key
            for key in receive
            if _is_pick(lookup.get(key, {})) and _pick_profile(lookup[key])[0] > 1
        ),
        "",
    )
    if weak_pick:
        weak = lookup[weak_pick]
        year = _pick_profile(weak)[1]
        upgrade = next(
            (
                key
                for key, row in lookup.items()
                if _is_pick(row) and _pick_profile(row)[:2] == (1, year) and key not in give
            ),
            "",
        )
        if upgrade:
            suggestions.append(
                CounterSuggestion(
                    "upgrade-future-capital",
                    "Upgrade future capital",
                    give,
                    tuple(upgrade if key == weak_pick else key for key in receive),
                    (
                        f"Replace {weak.get('player')} with target class "
                        f"{lookup[upgrade].get('player')}.",
                    ),
                    "A first-round target class improves future flexibility without assigning "
                    "it a player-equivalent value.",
                    "Target request only; opponent ownership is not encoded or claimed.",
                )
            )
    aging = next((row for row in receive_rows if _age_risk(row)), None)
    if aging and suggestions:
        suggestions.append(
            CounterSuggestion(
                "roster-window",
                f"{team_window} roster-window counter",
                suggestions[0].give,
                suggestions[0].receive,
                (
                    f"Use the minimal counter and ask whether {aging.get('player')} can be "
                    "replaced by a younger top-100 RB/WR/TE profile.",
                ),
                "This keeps the loadable trade exact while documenting the desired target profile.",
                "Target profile only; no opponent-owned player is asserted.",
            )
        )
    unique: list[CounterSuggestion] = []
    seen: set[tuple[tuple[str, ...], tuple[str, ...], str]] = set()
    for item in suggestions:
        signature = (item.give, item.receive, item.title)
        if signature not in seen:
            unique.append(item)
            seen.add(signature)
    return tuple(unique[:4])


def _decision_summary(recommendation: str, preferred: str, team_window: str) -> str:
    if recommendation == "COUNTER":
        return (
            f"NWR prefers {preferred.casefold()} for a {team_window.casefold()} roster; "
            "counter before accepting."
        )
    if recommendation == "TOO_CLOSE":
        return (
            "The evidence is too mixed for a reliable side preference in the "
            f"{team_window.casefold()} view."
        )
    action = "accept" if recommendation in {"ACCEPT", "LEAN_ACCEPT"} else "decline"
    return (
        f"NWR prefers {preferred.casefold()} and would {action} under the "
        f"{team_window.casefold()} view."
    )


def _synthesis_trace(dimensions: Sequence[DecisionDimension]) -> tuple[str, ...]:
    a = [row.label for row in dimensions if row.outcome.startswith("SIDE_A")]
    b = [row.label for row in dimensions if row.outcome.startswith("SIDE_B")]
    neutral = [row.label for row in dimensions if row.outcome in {"EVEN", "UNKNOWN"}]
    return (
        f"Current-side support ({len(a)}): {', '.join(a) or 'none'}.",
        f"Incoming-side support ({len(b)}): {', '.join(b) or 'none'}.",
        f"Even/unknown ({len(neutral)}): {', '.join(neutral) or 'none'}.",
        "No package score, side total, or rookie/pick-to-veteran conversion is used.",
    )


def _insufficient(team_window: str, reason: str) -> TradeDecision:
    return TradeDecision(
        AUTHORITY,
        "INSUFFICIENT_EVIDENCE",
        "No side",
        "LOW",
        team_window,
        reason,
        (reason,),
        reason,
        ("Add governed assets to both sides.",),
        (),
        ("No recommendation was synthesized.",),
        (),
    )


def _evidence_is_insufficient(
    give: Sequence[Mapping[str, object]],
    receive: Sequence[Mapping[str, object]],
    dimensions: Sequence[DecisionDimension],
) -> bool:
    all_rows = (*give, *receive)
    if all(_is_blocked(row) for row in all_rows):
        return True
    if all(_is_pick(row) for row in all_rows):
        future = next(row for row in dimensions if row.code == "D6")
        return future.outcome in {"UNKNOWN", "EVEN"}
    known = sum(row.outcome != "UNKNOWN" for row in dimensions)
    admitted = any(_rank(row) is not None or _is_rookie(row) or _is_pick(row) for row in all_rows)
    return known < 4 or not admitted


def _ranked_rows(rows: Sequence[Mapping[str, object]]) -> list[tuple[str, int]]:
    return [
        (str(row.get("player") or row.get("label")), int(rank))
        for row in rows
        if (rank := _rank(row)) is not None
    ]


def _best_ranked(rows: Sequence[Mapping[str, object]]) -> tuple[str, int] | None:
    ranked = _ranked_rows(rows)
    return min(ranked, key=lambda item: item[1]) if ranked else None


def _best_ranked_key(keys: Sequence[str], lookup: Mapping[str, Mapping[str, object]]) -> str:
    ranked = [(key, _rank(lookup.get(key, {}))) for key in keys]
    admitted = [(key, rank) for key, rank in ranked if rank is not None]
    return min(admitted, key=lambda item: item[1])[0] if admitted else ""


def _rank(row: Mapping[str, object]) -> int | None:
    value = _number(row.get("dynasty_rank"))
    return int(value) if value is not None and value > 0 else None


def _rank_band(rank: int) -> tuple[int, str]:
    for index, (limit, label) in enumerate(
        (
            (25, "Top 25"),
            (50, "Top 50"),
            (100, "Top 100"),
            (150, "Top 150"),
            (999, "Outside Top 150"),
        )
    ):
        if rank <= limit:
            return index, label
    return 5, "Unranked"


def _market_band(rank: float) -> int:
    for index, limit in enumerate((25, 50, 100, 150, 999)):
        if rank <= limit:
            return index
    return 5


def _best_market(rows: Sequence[Mapping[str, object]]) -> tuple[str, float, str] | None:
    values = [
        (str(row.get("player")), rank, str(row.get("market_status") or "display-only"))
        for row in rows
        if (rank := _number(row.get("market_dp_rank"))) is not None
    ]
    return min(values, key=lambda item: item[1]) if values else None


def _is_rookie(row: Mapping[str, object]) -> bool:
    return str(row.get("registry_asset_type")) == "Rookie Review"


def _is_blocked(row: Mapping[str, object]) -> bool:
    return str(row.get("registry_asset_type")) == "Blocked Rookie"


def _is_pick(row: Mapping[str, object]) -> bool:
    return str(row.get("asset_type")) == "Pick context" or str(row.get("position")) == "PICK"


def _pick_profile(row: Mapping[str, object]) -> tuple[int, int, str]:
    name = str(row.get("player") or row.get("asset_name") or row.get("label") or "Pick")
    asset_id = str(row.get("asset_id") or "")
    match = re.search(r"pick:(\d{4}):([1-5])(?:st|nd|rd|th)?$", asset_id)
    if match:
        return int(match.group(2)), int(match.group(1)), name
    match = re.search(r"(20\d{2})\s+([1-5])\.", name)
    if match:
        return int(match.group(2)), int(match.group(1)), name
    match = re.search(r"(20\d{2}).*?([1-5])(?:st|nd|rd|th)", name, re.IGNORECASE)
    if match:
        return int(match.group(2)), int(match.group(1)), name
    return 99, 9999, name


def _is_first_round_pick(row: Mapping[str, object]) -> bool:
    return _is_pick(row) and _pick_profile(row)[0] == 1


def _known_age(row: Mapping[str, object]) -> float | None:
    return _number(row.get("age"))


def _age_risk(row: Mapping[str, object]) -> bool:
    caveats = " ".join(str(value) for value in tuple(row.get("owner_caveats", ())))
    return "age-related" in caveats.casefold() or "age-window" in caveats.casefold()


def _youth_and_age_risk(rows: Sequence[Mapping[str, object]]) -> tuple[int, int]:
    young = sum(_is_rookie(row) for row in rows)
    young += sum(
        bool(age is not None and age <= 25) for row in rows if (age := _known_age(row)) is not None
    )
    return young, sum(_age_risk(row) for row in rows)


def _limited_one_qb(row: Mapping[str, object]) -> bool:
    if str(row.get("position")) != "QB":
        return False
    caveats = " ".join(str(value) for value in tuple(row.get("owner_caveats", ())))
    position_rank = str(row.get("position_rank") or "")
    match = re.search(r"(\d+)", position_rank)
    return "1qb" in caveats.casefold() or bool(match and int(match.group(1)) > 10)


def _risk_count(rows: Sequence[Mapping[str, object]]) -> int:
    return sum(_age_risk(row) or _is_blocked(row) or _limited_one_qb(row) for row in rows)


def _direction_value(outcome: str) -> int:
    return {
        "SIDE_A_CLEAR": -2,
        "SIDE_A_LEAN": -1,
        "EVEN": 0,
        "UNKNOWN": 0,
        "SIDE_B_LEAN": 1,
        "SIDE_B_CLEAR": 2,
    }[outcome]


def _number(value: object) -> float | None:
    try:
        text = str(value if value is not None else "").strip().replace(",", "")
        return float(text) if text and text.casefold() not in {"nan", "none"} else None
    except (TypeError, ValueError):
        return None
