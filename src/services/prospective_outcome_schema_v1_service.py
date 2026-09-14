"""Prospective Outcome V1 -- decision-type-specific outcome schemas.

This module is the SCHEMA half of the prospective outcome-evaluation
foundation (the ingestion/matching half lives in
`prospective_outcome_ingestion_v1_service.py`; the append-only storage half
is the existing `in_season_decision_trace_service.record_outcome`, extended
this pass with an optional `detail` payload).

Per the governing directive, this is deliberately NOT one generic
accuracy/correctness score. Different decision types have fundamentally
different outcome semantics, so each `TOOL_TYPES` member (see
`in_season_decision_trace_service.py`) gets its OWN dataclass shape here:

- `StartSitOutcomeDetail` -- recommended vs. actual starting lineup,
  eligible bench alternatives AT LOCK TIME, a real point-delta "lineup
  opportunity cost" (never a synthesized quality score).
- `WaiverOutcomeDetail` -- was a claim actually submitted/won, FAAB paid,
  bounded-horizon subsequent roster usage/value of the acquired player.
- `AddDropOutcomeDetail` -- added-player subsequent value, dropped-player
  subsequent value, roster usage, reversibility (a later re-add).
- `FaabOutcomeDetail` -- KEEPS player-decision-quality (was the pickup
  itself good, `FaabPlayerDecisionQuality`) and bid-range-calibration (was
  the suggested $ range accurate, `FaabBidRangeCalibration`) as two
  genuinely SEPARATE nested records, per the directive's explicit
  instruction not to conflate them.
- `TradeOutcomeDetail` -- a REJECTED trade only ever gets an
  `acceptance_status`/adoption signal; `realized_roster_outcome` (the real,
  observed post-trade roster value) is populated ONLY when
  `trade_accepted` is `True` -- this module never scores an unobserved
  counterfactual.
- `TradeFinderOutcomeDetail` -- package disposition (ignored / considered /
  sent / accepted); only reuses `TradeOutcomeDetail`'s realized-roster-
  outcome logic when the package was actually accepted.
- `StreamerOutcomeDetail` -- K_STREAMER/DST_STREAMER are evaluated
  INDEPENDENTLY of each other (one instance per position per week):
  recommended vs. actual starter vs. the prior roster option vs. what was
  actually available AT RECOMMENDATION TIME (never a hindsight-best
  alternative).
- `DraftOutcomeDetail` -- a thin, intentionally UNDER-populated envelope
  this pass. Real season-long roster-utility computation belongs to
  `marginal_roster_utility_v2`, which this pass's hard boundary explicitly
  forbids touching -- so this schema exists (the shape a future,
  boundary-cleared pass can fill in) but this pass performs no draft
  outcome computation of its own. `evaluation_method` names the deferred
  standard (season-long roster utility evaluated separately from injury
  luck, chronological/no-hindsight) rather than silently defaulting to
  nothing.

Every dataclass is a frozen, pure data container -- no I/O, no judgment
computed beyond plain arithmetic over already-real numbers (e.g. a point
delta). `to_detail_dict()` is the exact camelCase-free (this backend layer
uses plain snake_case-derived JSON keys the same way the rest of
`in_season_decision_trace_service.py` does -- the facade layer is
responsible for any camelCase projection, same precedent as
`_decision_trace_history_event_payload`) payload handed to
`record_outcome(..., detail=...)`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence


def _round_or_none(value: float | None, digits: int = 2) -> float | None:
    if value is None:
        return None
    return round(float(value), digits)


def _points_by_player_list(mapping: Mapping[str, float | None]) -> list[dict[str, Any]]:
    """Real bug found + fixed this pass (History UI V2 / Work Unit 15's
    snake_case<->camelCase JSON-boundary property test): a dict KEYED BY a
    literal player id (e.g. Sleeper's DST ids, which are bare team codes
    like "NE") is exactly the shape this codebase has already been bitten
    by more than once -- `application/contracts.py`'s generic
    `camel_case_key` treats every dict key as a schema field name, not
    literal data, and mangles an all-caps single-token key by lowercasing
    only its first letter ("NE" -> "nE", "WR" -> "wR", "QB" -> "qB" -- see
    `test_desktop_application_api.py`'s and
    `test_redraft_draft_room_v1_service.py`'s own real, previously-found
    instances of this exact bug class). Per that same established,
    already-precedented fix (never modify the shared `camel_case_key`
    itself -- narrowly change the call site to stop using a literal value
    as a dict key), this returns a flat LIST of `{playerId, points}"`
    objects instead of a dict keyed by player id -- immune to key-casing
    entirely, since "playerId"/"points" are real, intentional field names,
    never literal data. Sorted by player id for deterministic output."""

    return [
        {"playerId": str(player_id), "points": _round_or_none(points)}
        for player_id, points in sorted(mapping.items(), key=lambda item: str(item[0]))
    ]


# ---------------------------------------------------------------------------
# START_SIT
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StartSitOutcomeDetail:
    KIND = "START_SIT_LINEUP_V1"

    week: int | None
    recommended_starter_ids: tuple[str, ...]
    actual_starter_ids: tuple[str, ...]
    # The bench at lock time -- derived ONLY from the trace's own frozen
    # `roster_state_player_ids` minus its own frozen `recommendation.starters`,
    # never from a "current" roster read (see the ingestion module's
    # no-future-leakage guarantee).
    eligible_alternative_ids_at_lock: tuple[str, ...]
    recommended_only_ids: tuple[str, ...]  # NWR recommended, owner benched
    actual_only_ids: tuple[str, ...]  # owner started, NWR did not recommend
    recommended_projected_total: float | None
    actual_points_total: float | None
    actual_points_by_player_id: dict[str, float]
    # Points the recommended-but-benched players actually scored minus
    # points the started-but-not-recommended players actually scored.
    # Positive => following the recommendation would have outscored the
    # owner's real deviation. `None` only when not computable (missing
    # real points data for one of the differing players).
    lineup_opportunity_cost: float | None

    def to_detail_dict(self) -> dict[str, Any]:
        return {
            "kind": self.KIND,
            "week": self.week,
            "recommendedStarterIds": list(self.recommended_starter_ids),
            "actualStarterIds": list(self.actual_starter_ids),
            "eligibleAlternativeIdsAtLock": list(self.eligible_alternative_ids_at_lock),
            "recommendedOnlyIds": list(self.recommended_only_ids),
            "actualOnlyIds": list(self.actual_only_ids),
            "recommendedProjectedTotal": _round_or_none(self.recommended_projected_total),
            "actualPointsTotal": _round_or_none(self.actual_points_total),
            # A LIST, not a dict keyed by player id -- see
            # `_points_by_player_list`'s own docstring for the real bug
            # this shape avoids.
            "actualPointsByPlayer": _points_by_player_list(self.actual_points_by_player_id),
            "lineupOpportunityCost": _round_or_none(self.lineup_opportunity_cost),
        }


# ---------------------------------------------------------------------------
# WAIVER
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class WaiverOutcomeDetail:
    KIND = "WAIVER_V1"

    recommended_player_id: str | None
    claim_submitted: bool | None
    claim_won: bool | None
    faab_paid: float | None
    horizon_weeks: int
    subsequent_roster_usage_weeks: int | None
    subsequent_total_points: float | None

    def to_detail_dict(self) -> dict[str, Any]:
        return {
            "kind": self.KIND,
            "recommendedPlayerId": self.recommended_player_id,
            "claimSubmitted": self.claim_submitted,
            "claimWon": self.claim_won,
            "faabPaid": _round_or_none(self.faab_paid),
            "horizonWeeks": self.horizon_weeks,
            "subsequentRosterUsageWeeks": self.subsequent_roster_usage_weeks,
            "subsequentTotalPoints": _round_or_none(self.subsequent_total_points),
        }


# ---------------------------------------------------------------------------
# ADD_DROP
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AddDropOutcomeDetail:
    KIND = "ADD_DROP_V1"

    added_player_id: str | None
    dropped_player_id: str | None
    horizon_weeks: int
    added_player_subsequent_points: float | None
    added_player_subsequent_roster_usage_weeks: int | None
    dropped_player_subsequent_points: float | None
    # Was the dropped player later RE-ADDED by the same roster within the
    # observed horizon -- a real, observed reversal, not a judgment call.
    dropped_player_reversed: bool | None

    def to_detail_dict(self) -> dict[str, Any]:
        return {
            "kind": self.KIND,
            "addedPlayerId": self.added_player_id,
            "droppedPlayerId": self.dropped_player_id,
            "horizonWeeks": self.horizon_weeks,
            "addedPlayerSubsequentPoints": _round_or_none(self.added_player_subsequent_points),
            "addedPlayerSubsequentRosterUsageWeeks": self.added_player_subsequent_roster_usage_weeks,
            "droppedPlayerSubsequentPoints": _round_or_none(self.dropped_player_subsequent_points),
            "droppedPlayerReversed": self.dropped_player_reversed,
        }


# ---------------------------------------------------------------------------
# FAAB -- deliberately two SEPARATE axes, never merged into one figure.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FaabPlayerDecisionQuality:
    """Was the underlying player pickup itself good -- independent of
    whatever dollar amount was suggested or paid."""

    subsequent_points: float | None
    subsequent_roster_usage_weeks: int | None
    horizon_weeks: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "subsequentPoints": _round_or_none(self.subsequent_points),
            "subsequentRosterUsageWeeks": self.subsequent_roster_usage_weeks,
            "horizonWeeks": self.horizon_weeks,
        }


@dataclass(frozen=True)
class FaabBidRangeCalibration:
    """Was the suggested $ range accurate relative to what was actually
    needed to win -- independent of whether the pickup itself was good."""

    suggested_bid_low: float | None
    suggested_bid_high: float | None
    amount_bid: float | None
    won: bool | None
    # The real winning bid amount for this player in this waiver period,
    # from real league transaction data -- observable regardless of whether
    # the recommended owner actually won (another roster's real winning
    # claim is still real, public league data).
    actual_winning_bid: float | None
    bid_within_suggested_range: bool | None
    margin_vs_actual_winning_bid: float | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "suggestedBidLow": _round_or_none(self.suggested_bid_low),
            "suggestedBidHigh": _round_or_none(self.suggested_bid_high),
            "amountBid": _round_or_none(self.amount_bid),
            "won": self.won,
            "actualWinningBid": _round_or_none(self.actual_winning_bid),
            "bidWithinSuggestedRange": self.bid_within_suggested_range,
            "marginVsActualWinningBid": _round_or_none(self.margin_vs_actual_winning_bid),
        }


@dataclass(frozen=True)
class FaabOutcomeDetail:
    KIND = "FAAB_V1"

    recommended_player_id: str | None
    player_decision_quality: FaabPlayerDecisionQuality
    bid_range_calibration: FaabBidRangeCalibration

    def to_detail_dict(self) -> dict[str, Any]:
        return {
            "kind": self.KIND,
            "recommendedPlayerId": self.recommended_player_id,
            "playerDecisionQuality": self.player_decision_quality.to_dict(),
            "bidRangeCalibration": self.bid_range_calibration.to_dict(),
        }


# ---------------------------------------------------------------------------
# TRADE -- a rejected trade never gets a realized-roster-outcome verdict.
# ---------------------------------------------------------------------------

TRADE_ACCEPTANCE_STATUSES = frozenset({"ACCEPTED", "REJECTED", "UNKNOWN"})


@dataclass(frozen=True)
class TradeRealizedRosterOutcome:
    horizon_weeks: int
    gives_subsequent_points: dict[str, float | None]
    receives_subsequent_points: dict[str, float | None]
    # sum(receives) - sum(gives); None unless every player's subsequent
    # points value is actually known.
    net_subsequent_points_delta: float | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "horizonWeeks": self.horizon_weeks,
            # LISTS, not dicts keyed by player id -- see
            # `_points_by_player_list`'s own docstring for the real bug
            # this shape avoids.
            "givesSubsequentPointsByPlayer": _points_by_player_list(self.gives_subsequent_points),
            "receivesSubsequentPointsByPlayer": _points_by_player_list(self.receives_subsequent_points),
            "netSubsequentPointsDelta": _round_or_none(self.net_subsequent_points_delta),
        }


@dataclass(frozen=True)
class TradeOutcomeDetail:
    KIND = "TRADE_V1"

    acceptance_status: str  # one of TRADE_ACCEPTANCE_STATUSES
    trade_accepted: bool | None
    # Only ever non-None when trade_accepted is True -- a rejected/unknown
    # trade is never scored against an unobserved counterfactual.
    realized_roster_outcome: TradeRealizedRosterOutcome | None

    def __post_init__(self) -> None:
        if self.acceptance_status not in TRADE_ACCEPTANCE_STATUSES:
            raise ValueError(f"Unknown trade acceptance status: {self.acceptance_status!r}")
        if self.realized_roster_outcome is not None and self.trade_accepted is not True:
            raise ValueError(
                "realized_roster_outcome may only be populated for an ACTUALLY ACCEPTED trade "
                "(trade_accepted=True) -- a rejected/unknown trade cannot be scored against an "
                "unobserved counterfactual."
            )

    def to_detail_dict(self) -> dict[str, Any]:
        return {
            "kind": self.KIND,
            "acceptanceStatus": self.acceptance_status,
            "tradeAccepted": self.trade_accepted,
            "realizedRosterOutcome": (
                self.realized_roster_outcome.to_dict() if self.realized_roster_outcome is not None else None
            ),
        }


# ---------------------------------------------------------------------------
# TRADE_FINDER / TRADE_PACKAGE_SEARCH
# ---------------------------------------------------------------------------

TRADE_PACKAGE_DISPOSITIONS = frozenset({"IGNORED", "CONSIDERED", "SENT", "ACCEPTED", "UNKNOWN"})


@dataclass(frozen=True)
class TradeFinderOutcomeDetail:
    KIND = "TRADE_FINDER_V1"

    package_disposition: str  # one of TRADE_PACKAGE_DISPOSITIONS
    # Only populated (and only ever with trade_accepted=True inside it) when
    # package_disposition == "ACCEPTED".
    linked_trade_outcome: TradeOutcomeDetail | None

    def __post_init__(self) -> None:
        if self.package_disposition not in TRADE_PACKAGE_DISPOSITIONS:
            raise ValueError(f"Unknown trade package disposition: {self.package_disposition!r}")
        if self.linked_trade_outcome is not None and self.package_disposition != "ACCEPTED":
            raise ValueError("linked_trade_outcome may only be set when package_disposition == 'ACCEPTED'.")

    def to_detail_dict(self) -> dict[str, Any]:
        return {
            "kind": self.KIND,
            "packageDisposition": self.package_disposition,
            "linkedTradeOutcome": (
                self.linked_trade_outcome.to_detail_dict() if self.linked_trade_outcome is not None else None
            ),
        }


# ---------------------------------------------------------------------------
# K_STREAMER / DST_STREAMER -- evaluated independently of each other; one
# instance per position per week, same shape reused (not merged together).
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StreamerOutcomeDetail:
    KIND = "STREAMER_V1"

    position: str  # "K" | "DST"
    week: int | None
    recommended_player_id: str | None
    recommended_player_actual_points: float | None
    actual_starter_player_id: str | None
    actual_starter_actual_points: float | None
    # The player actually ON the roster at recommendation time, before any
    # streaming pickup -- from the trace's own frozen roster state.
    prior_roster_option_player_id: str | None
    prior_roster_option_actual_points: float | None
    # What was genuinely available AT RECOMMENDATION TIME (the trace's own
    # frozen alternatives), never a hindsight-best pick from the full week's
    # results.
    available_alternative_ids_at_recommendation: tuple[str, ...]
    best_available_alternative_id: str | None
    best_available_alternative_actual_points: float | None

    def to_detail_dict(self) -> dict[str, Any]:
        return {
            "kind": self.KIND,
            "position": self.position,
            "week": self.week,
            "recommendedPlayerId": self.recommended_player_id,
            "recommendedPlayerActualPoints": _round_or_none(self.recommended_player_actual_points),
            "actualStarterPlayerId": self.actual_starter_player_id,
            "actualStarterActualPoints": _round_or_none(self.actual_starter_actual_points),
            "priorRosterOptionPlayerId": self.prior_roster_option_player_id,
            "priorRosterOptionActualPoints": _round_or_none(self.prior_roster_option_actual_points),
            "availableAlternativeIdsAtRecommendation": list(self.available_alternative_ids_at_recommendation),
            "bestAvailableAlternativeId": self.best_available_alternative_id,
            "bestAvailableAlternativeActualPoints": _round_or_none(self.best_available_alternative_actual_points),
        }


# ---------------------------------------------------------------------------
# DRAFT -- schema-only this pass; see module docstring. Preserves the
# chronological/no-hindsight standard (season-long roster utility evaluated
# separately from injury luck) as a NAMED, deferred method rather than
# silently defaulting to nothing.
# ---------------------------------------------------------------------------

DRAFT_EVALUATION_METHOD_DEFERRED = "DEFERRED_TO_SEASON_LONG_ROSTER_UTILITY_ENGINE"


@dataclass(frozen=True)
class DraftOutcomeDetail:
    KIND = "DRAFT_V1"

    evaluation_method: str
    season_long_roster_utility: float | None
    injury_luck_adjustment: float | None
    notes: str

    def to_detail_dict(self) -> dict[str, Any]:
        return {
            "kind": self.KIND,
            "evaluationMethod": self.evaluation_method,
            "seasonLongRosterUtility": _round_or_none(self.season_long_roster_utility),
            "injuryLuckAdjustment": _round_or_none(self.injury_luck_adjustment),
            "notes": self.notes,
        }


def build_deferred_draft_outcome_detail(notes: str = "") -> DraftOutcomeDetail:
    """The only DRAFT outcome builder this pass ships: an explicitly
    unpopulated placeholder naming the deferred evaluation method. Real
    season-long roster-utility computation lives in
    `marginal_roster_utility_v2`, out of this pass's hard boundary -- a
    future, boundary-cleared pass fills this schema in for real, it is not
    computed here."""

    return DraftOutcomeDetail(
        evaluation_method=DRAFT_EVALUATION_METHOD_DEFERRED,
        season_long_roster_utility=None,
        injury_luck_adjustment=None,
        notes=notes,
    )
